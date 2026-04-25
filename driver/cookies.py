import time
def expire(cookies:any) :
    if not isinstance(cookies, list) and  not isinstance(cookies, dict):
        raise TypeError("cookies参数必须是列表类型")
    
    cookie_expiry=None
    for cookie in cookies:
        if not isinstance(cookie, dict):
            continue
        if cookie['name'] == 'slave_sid' and 'expires' in str(cookie):
               try:
                   expiry_time = float(cookie['expires'])
                   remaining_time = expiry_time - time.time()
                   if remaining_time > 0:
                       cookie_expiry = {
                           'expiry_timestamp': expiry_time,
                           'remaining_seconds': int(remaining_time),
                           'expiry_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiry_time))
                       }
                   break
               except ValueError:
                   print(f"slave_sid 的过期时间戳无效: {cookie['expiry']}")
                   break
    return cookie_expiry


