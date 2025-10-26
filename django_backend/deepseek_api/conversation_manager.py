"""
多轮对话管理器
负责管理对话上下文、窗口限制、摘要压缩等功能
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConversationType(Enum):
    """对话类型枚举"""
    GENERAL_QA = "general_qa"           # 通用问答
    LOG_ANALYSIS = "log_analysis"       # 日志分析
    FOLLOW_UP = "follow_up"            # 追问/澄清
    SUMMARY_REQUEST = "summary_request" # 摘要请求

@dataclass
class ConversationTurn:
    """单轮对话数据结构"""
    user_input: str
    assistant_reply: str
    conversation_type: ConversationType
    timestamp: str
    metadata: Dict = None  # 存储额外信息，如检索到的日志数量等

class ConversationManager:
    """多轮对话管理器"""
    
    def __init__(self, max_context_length: int = 4000, max_turns: int = 10):
        """
        初始化对话管理器
        
        Args:
            max_context_length: 最大上下文长度（字符数）
            max_turns: 最大保留轮次
        """
        self.max_context_length = max_context_length
        self.max_turns = max_turns
    
    def classify_conversation_type(self, user_input: str, has_history: bool) -> ConversationType:
        """
        分类对话类型
        
        Args:
            user_input: 用户输入
            has_history: 是否有历史对话
            
        Returns:
            对话类型
        """
        user_input_lower = user_input.lower()
        
        # 检查是否是追问
        follow_up_keywords = ['继续', '详细', '更多', '具体', '怎么', '为什么', '那么', '还有']
        if has_history and any(keyword in user_input for keyword in follow_up_keywords):
            return ConversationType.FOLLOW_UP
        
        # 检查是否是摘要请求
        summary_keywords = ['总结', '摘要', '概括', 'summary', 'summarize']
        if any(keyword in user_input_lower for keyword in summary_keywords):
            return ConversationType.SUMMARY_REQUEST
        
        # 检查是否是日志分析
        log_keywords = ['日志', '错误', '异常', 'error', 'exception', 'log', '分析', 'analyze']
        if any(keyword in user_input_lower for keyword in log_keywords):
            return ConversationType.LOG_ANALYSIS
        
        # 默认为通用问答
        return ConversationType.GENERAL_QA
    
    def parse_conversation_history(self, context_string: str) -> List[ConversationTurn]:
        """
        解析对话历史字符串为结构化数据
        
        Args:
            context_string: 原始上下文字符串
            
        Returns:
            对话轮次列表
        """
        turns = []
        if not context_string.strip():
            return turns
        
        # 按照 "用户：...\\n回复：...\\n" 的格式解析
        parts = context_string.split('用户：')[1:]  # 跳过第一个空元素
        
        for part in parts:
            if '回复：' in part:
                user_part, reply_part = part.split('回复：', 1)
                user_input = user_part.strip()
                
                # 找到回复的结束位置（下一个"用户："或字符串结尾）
                reply_lines = reply_part.split('\n')
                assistant_reply = []
                
                for line in reply_lines:
                    if line.strip() == '':
                        continue
                    assistant_reply.append(line)
                
                if assistant_reply:
                    assistant_reply_text = '\n'.join(assistant_reply)
                    
                    # 推断对话类型（简化版）
                    conv_type = self.classify_conversation_type(user_input, len(turns) > 0)
                    
                    turn = ConversationTurn(
                        user_input=user_input,
                        assistant_reply=assistant_reply_text,
                        conversation_type=conv_type,
                        timestamp="",  # 历史数据没有时间戳
                        metadata={}
                    )
                    turns.append(turn)
        
        return turns
    
    def compress_context(self, turns: List[ConversationTurn]) -> List[ConversationTurn]:
        """
        压缩上下文，保留关键信息
        
        Args:
            turns: 对话轮次列表
            
        Returns:
            压缩后的对话轮次列表
        """
        if len(turns) <= self.max_turns:
            return turns
        
        # 策略1：保留最近的对话
        recent_turns = turns[-self.max_turns:]
        
        # 策略2：如果还是太长，进行摘要压缩
        total_length = sum(len(turn.user_input) + len(turn.assistant_reply) for turn in recent_turns)
        
        if total_length > self.max_context_length:
            # 保留最近3轮，其余进行摘要
            if len(recent_turns) > 3:
                summary_turns = recent_turns[:-3]
                keep_turns = recent_turns[-3:]
                
                # 生成摘要
                summary_text = self._generate_summary(summary_turns)
                summary_turn = ConversationTurn(
                    user_input="[历史对话摘要]",
                    assistant_reply=summary_text,
                    conversation_type=ConversationType.SUMMARY_REQUEST,
                    timestamp="",
                    metadata={"is_summary": True, "original_turns": len(summary_turns)}
                )
                
                return [summary_turn] + keep_turns
        
        return recent_turns
    
    def _generate_summary(self, turns: List[ConversationTurn]) -> str:
        """
        生成对话摘要
        
        Args:
            turns: 需要摘要的对话轮次
            
        Returns:
            摘要文本
        """
        if not turns:
            return "无历史对话"
        
        # 简化版摘要：提取关键主题和结论
        topics = []
        conclusions = []
        
        for turn in turns:
            # 提取主题（用户问题的关键词）
            user_keywords = self._extract_keywords(turn.user_input)
            if user_keywords:
                topics.extend(user_keywords)
            
            # 提取结论（回复的关键信息）
            if len(turn.assistant_reply) > 100:
                # 取前100字符作为摘要
                conclusions.append(turn.assistant_reply[:100] + "...")
        
        summary = f"讨论主题：{', '.join(set(topics[:5]))}。"
        if conclusions:
            summary += f" 主要结论：{conclusions[-1]}"
        
        return summary
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词（简化版）
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        # 简化的关键词提取
        keywords = []
        technical_terms = ['数据库', '索引', '连接', '性能', '错误', '日志', '服务', '系统']
        
        for term in technical_terms:
            if term in text:
                keywords.append(term)
        
        return keywords
    
    def build_context_for_llm(self, turns: List[ConversationTurn], current_input: str, 
                             conversation_type: ConversationType) -> str:
        """
        为LLM构建上下文字符串
        
        Args:
            turns: 历史对话轮次
            current_input: 当前用户输入
            conversation_type: 当前对话类型
            
        Returns:
            格式化的上下文字符串
        """
        if not turns:
            return f"用户：{current_input}\n回复："
        
        # 根据对话类型选择不同的上下文构建策略
        if conversation_type == ConversationType.FOLLOW_UP:
            # 追问时，重点关注最近的对话
            context_parts = []
            for turn in turns[-2:]:  # 只保留最近2轮
                context_parts.append(f"用户：{turn.user_input}")
                context_parts.append(f"回复：{turn.assistant_reply}")
            
            context_parts.append(f"用户：{current_input}")
            context_parts.append("回复：")
            return "\n".join(context_parts)
        
        elif conversation_type == ConversationType.SUMMARY_REQUEST:
            # 摘要请求时，包含更多历史信息
            context_parts = []
            for turn in turns:
                context_parts.append(f"用户：{turn.user_input}")
                context_parts.append(f"回复：{turn.assistant_reply}")
            
            context_parts.append(f"用户：{current_input}")
            context_parts.append("回复：")
            return "\n".join(context_parts)
        
        else:
            # 默认策略：包含压缩后的历史
            context_parts = []
            for turn in turns:
                context_parts.append(f"用户：{turn.user_input}")
                context_parts.append(f"回复：{turn.assistant_reply}")
            
            context_parts.append(f"用户：{current_input}")
            context_parts.append("回复：")
            return "\n".join(context_parts)
    
    def should_use_rag(self, conversation_type: ConversationType, user_input: str) -> bool:
        """
        判断是否需要使用RAG检索
        
        Args:
            conversation_type: 对话类型
            user_input: 用户输入
            
        Returns:
            是否使用RAG
        """
        # 日志分析类型的对话需要RAG
        if conversation_type == ConversationType.LOG_ANALYSIS:
            return True
        
        # 包含具体技术问题的通用问答也可能需要RAG
        technical_indicators = ['错误', '异常', '性能', '优化', 'error', 'exception', 'performance']
        if any(indicator in user_input.lower() for indicator in technical_indicators):
            return True
        
        # 追问和摘要通常不需要新的RAG检索
        return False
    
    def format_context_for_storage(self, turns: List[ConversationTurn]) -> str:
        """
        将结构化对话数据格式化为存储字符串
        
        Args:
            turns: 对话轮次列表
            
        Returns:
            格式化的存储字符串
        """
        context_parts = []
        for turn in turns:
            context_parts.append(f"用户：{turn.user_input}")
            context_parts.append(f"回复：{turn.assistant_reply}")
        
        return "\n".join(context_parts) + "\n"

    def add_new_turn(self, turns: List[ConversationTurn], user_input: str, 
                    assistant_reply: str, conversation_type: ConversationType,
                    timestamp: str, metadata: Dict = None) -> List[ConversationTurn]:
        """
        添加新的对话轮次
        
        Args:
            turns: 现有对话轮次
            user_input: 用户输入
            assistant_reply: 助手回复
            conversation_type: 对话类型
            timestamp: 时间戳
            metadata: 元数据
            
        Returns:
            更新后的对话轮次列表
        """
        new_turn = ConversationTurn(
            user_input=user_input,
            assistant_reply=assistant_reply,
            conversation_type=conversation_type,
            timestamp=timestamp,
            metadata=metadata or {}
        )
        
        updated_turns = turns + [new_turn]
        return self.compress_context(updated_turns)
