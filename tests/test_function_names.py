#!/usr/bin/env python3
"""
测试团队函数名生成逻辑
"""
import re

def generate_func_name(team_name: str) -> str:
    """模拟 hierarchy_system.py 中的函数名生成逻辑"""
    import hashlib
    
    # 移除所有非ASCII字符，保留字母、数字、下划线
    func_name_base = re.sub(r'[^a-zA-Z0-9_]', '_', team_name.lower())
    # 清理多余的下划线
    func_name_base = re.sub(r'_+', '_', func_name_base).strip('_')
    
    # 如果移除非ASCII后为空（纯中文名称），使用哈希值确保唯一性
    if not func_name_base or not any(c.isalpha() for c in func_name_base):
        # 使用团队名称的哈希值生成唯一标识
        name_hash = hashlib.md5(team_name.encode('utf-8')).hexdigest()[:8]
        func_name = f'team_{name_hash}'
    else:
        # 确保以字母开头
        if not func_name_base[0].isalpha():
            func_name_base = 'team_' + func_name_base
        func_name = func_name_base + '_team'
    
    return func_name


def test_function_names():
    """测试各种团队名称的函数名生成"""
    test_cases = [
        "理论物理学团队",  # 纯中文，使用哈希
        "实验物理学团队",  # 纯中文，使用哈希
        "专家评审团队",    # 纯中文，使用哈希
        "Theoretical Physics Team",  # 英文
        "Experimental Team",  # 英文
        "Data Analysis",  # 英文
        "数据-分析_团队",  # 混合，但移除后为空
        "Team-A",  # 英文带符号
        "123Team",  # 数字开头
        "",  # 空名称
        "AI研究组",  # 英文+中文
        "Backend开发团队",  # 英文+中文
    ]
    
    print("=" * 80)
    print("团队函数名生成测试")
    print("=" * 80)
    
    all_passed = True
    generated_names = {}
    
    for team_name in test_cases:
        func_name = generate_func_name(team_name)
        # 检查是否符合 AWS Bedrock 要求：只包含 [a-zA-Z0-9_-]
        is_valid = bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', func_name))
        
        # 检查唯一性
        is_unique = func_name not in generated_names.values()
        generated_names[team_name] = func_name
        
        status = "✅" if (is_valid and is_unique) else "❌"
        print(f"\n{status} 团队名称: '{team_name}'")
        print(f"   生成函数名: {func_name}")
        print(f"   符合规范: {is_valid}")
        print(f"   唯一性: {is_unique}")
        
        if not is_valid or not is_unique:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 80)
    
    return all_passed


if __name__ == "__main__":
    success = test_function_names()
    exit(0 if success else 1)
