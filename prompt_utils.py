import re
import json
import ast

def extract_fn(text):
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    if len(matches) > 0:
        return matches[0]
    else:
        return None
      
def fix_guidance(text):
    # Find the value of the "guidance" field and replace the newline characters with \n
    fixed_text = re.sub(
        r'("guidance":\s*")[^"]*', lambda m: m.group(0).replace("\n", "\\n"), text
    )
    return fixed_text
  
  

def verify_fn(result, mode=None):
    temp = extract_fn(result)
    if temp:
        try:
            temp = json.loads(temp)
            return temp
        except:
            try:
                temp = ast.literal_eval(temp)
                return temp
            except:
                ## 应对guidance内有未转义\n
                if mode == "guidance":
                    try:
                        temp = extract_fn(fix_guidance(result))
                        temp = json.loads(temp)
                        return temp
                    except:
                        return "Error"
                ## 应对最后花括号前缺少双引号
                try:
                    temp = re.sub(r"(\s*})", r'" \1', temp)
                    temp = json.loads(temp)
                    return temp
                except:
                    return "Error"
    else:
        result_temp = result
        if not result_temp.strip().startswith("{"):
            result_temp = "{" + result
        if not result_temp.strip().endswith("}"):
            result_temp = result_temp + "}"
        try:
            result_temp = json.loads(result_temp)
            return result_temp
        except:
            return "Error"