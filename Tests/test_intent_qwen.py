#!/usr/bin/env python3
"""
快速测试 qwen2.5:0.5b 意图分类器
"""

import sys
import os
import django

# 添加项目路径
sys.path.append('/Users/chenkaixuan/Desktop/DataAnalysis/Master/Django-Data-Analysis/django_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deepseek_project.settings')

# 初始化Django
django.setup()

from deepseek_api.intent_classifier import classify_user_intent, get_intent_classifier

def test_qwen_intent_classifier():
    """测试qwen2.5:0.5b意图分类器"""
    
    print("🚀 测试 qwen2.5:0.5b 意图分类器")
    print("=" * 60)
    
    # 获取分类器信息
    classifier = get_intent_classifier()
    model_info = classifier.get_model_info()
    
    print(f"📊 模型信息:")
    print(f"   模型名称: {model_info['model_name']}")
    print(f"   Ollama地址: {model_info['ollama_url']}")
    print(f"   模型类型: {model_info['model_type']}")
    print(f"   初始化状态: {model_info['initialized']}")
    print()
    
    # 测试用例
    test_cases = [
        # 中文测试
        ("数据库连接错误怎么解决？", "log_analysis"),
        ("你好，请问你是谁？", "greeting"),
        ("能详细说说刚才的解决方案吗？", "follow_up"),
        ("总结一下我们的对话", "summary_request"),
        ("如何配置nginx服务器？", "technical_help"),
        
        # 英文测试
        ("How to solve database index error?", "log_analysis"),
        ("Hello, nice to meet you!", "greeting"),
        ("Can you explain more details?", "follow_up"),
        
        # 边界测试
        ("", "unknown"),
        ("？？？", "unknown"),
    ]
    
    print("🧪 开始测试...")
    print("-" * 60)
    
    total_time = 0
    correct_predictions = 0
    
    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"测试 {i:2d}: {text[:40]:<40}")
        
        try:
            result = classify_user_intent(text)
            
            is_correct = result.intent.value == expected
            if is_correct:
                correct_predictions += 1
            
            total_time += result.processing_time
            
            status = "✅" if is_correct else "❌"
            print(f"        预期: {expected:<15} 实际: {result.intent.value:<15} {status}")
            print(f"        置信度: {result.confidence:.3f}  耗时: {result.processing_time:.3f}秒  模型: {result.model_used}")
            
        except Exception as e:
            print(f"        ❌ 错误: {e}")
        
        print()
    
    # 统计结果
    accuracy = correct_predictions / len(test_cases)
    avg_time = total_time / len(test_cases)
    
    print("=" * 60)
    print("📈 测试结果统计:")
    print(f"   总测试数: {len(test_cases)}")
    print(f"   正确预测: {correct_predictions}")
    print(f"   准确率: {accuracy:.1%}")
    print(f"   平均耗时: {avg_time:.3f}秒")
    print(f"   总耗时: {total_time:.3f}秒")
    
    if accuracy >= 0.7:
        print("🎉 测试通过！意图分类器工作正常")
    else:
        print("⚠️  准确率较低，可能需要检查模型或网络连接")
    
    return accuracy, avg_time

def check_ollama_status():
    """检查Ollama服务状态"""
    import requests
    
    print("🔍 检查 Ollama 服务状态...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            
            print("✅ Ollama 服务运行正常")
            print(f"📦 已安装模型: {model_names}")
            
            if 'qwen2.5:0.5b' in model_names:
                print("✅ qwen2.5:0.5b 模型已安装")
                return True
            else:
                print("❌ qwen2.5:0.5b 模型未安装")
                print("💡 请运行: ollama pull qwen2.5:0.5b")
                return False
        else:
            print(f"❌ Ollama 服务响应异常: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ 无法连接到 Ollama 服务: {e}")
        print("💡 请确保 Ollama 服务已启动: ollama serve")
        return False

if __name__ == "__main__":
    print("🧪 qwen2.5:0.5b 意图分类器集成测试")
    print("=" * 60)
    
    # 检查Ollama状态
    ollama_ok = check_ollama_status()
    print()
    
    if ollama_ok:
        # 运行测试
        accuracy, avg_time = test_qwen_intent_classifier()
        
        print("\n🎯 性能评估:")
        if avg_time < 0.1:
            print("⚡ 延迟极低 (< 100ms)")
        elif avg_time < 0.5:
            print("🚀 延迟较低 (< 500ms)")
        else:
            print("🐌 延迟较高 (> 500ms)")
            
        if accuracy >= 0.8:
            print("🎯 准确率优秀 (≥ 80%)")
        elif accuracy >= 0.6:
            print("👍 准确率良好 (≥ 60%)")
        else:
            print("📈 准确率需要改进 (< 60%)")
    else:
        print("❌ Ollama 服务不可用，请先安装并启动")
        print("\n📝 安装步骤:")
        print("1. 启动 Ollama: ollama serve")
        print("2. 安装模型: ollama pull qwen2.5:0.5b")
        print("3. 重新运行测试")
