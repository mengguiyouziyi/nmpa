# NMPA爬虫技术深度分析报告

## 项目概览

本报告深度分析了9个NMPA（国家药品监督管理局）爬虫项目，重点提取了突破NMPA签名算法和反爬虫机制的关键技术细节。

## 1. 签名算法实现

### 1.1 发现的签名算法（来自magical_spider项目）

```python
def get_sign(self, dic):
    """生成签名"""
    array = []
    for key in dic:
        array.append(key + '=' + str(dic[key]))
    array = self.paramsStrSort('&'.join(array))
    return self.jsonmd5ToString(array)

def jsonmd5ToString(self, ready_to_encode):
    """MD5签名生成"""
    ready_to_encode = ready_to_encode + "&nmpasecret2020"
    a = parse.quote(ready_to_encode)
    m = hashlib.md5()
    m.update(a.encode('utf-8'))
    return m.hexdigest()

def paramsStrSort(self, a):
    """参数排序"""
    a = a.split("&")
    a.sort()
    b = ''
    for i in a:
        b = b + str(i) + "&"
    return b[:-1]
```

**关键技术要点：**
- 签名密钥：`nmpasecret2020`
- 算法流程：参数按键排序 → 拼接字符串 → 添加密钥 → URL编码 → MD5加密
- 适用于需要签名的API接口

## 2. API端点和参数构造

### 2.1 生产许可证API（来自QueenOfBugs项目）

**核心API端点：**
```python
# 列表API
list_url = "http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList"

# 详情API
detail_url = "http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsById"
```

**请求头配置：**
```python
headers = {
    'Origin': 'http://scxk.nmpa.gov.cn:81',
    'Referer': 'http://scxk.nmpa.gov.cn:81/xk/',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
}
```

**参数构造方法：**
```python
def get_all_id(kw: str) -> list:
    """获取ID列表"""
    ids = list()
    page_count = get_pages_status(kw)["page_count"]
    total_count = get_pages_status(kw)["total_count"]

    if page_count <= 50 and page_count > 0:
        ids = get_pages(page_count, kw)
    else:
        # 分年查询策略
        year = 2016
        while len(ids) < total_count:
            kw_year = kw + str(year)
            total_amount = get_pages_status(kw_year)["total_count"]
            page_amount = get_pages_status(kw_year)["page_count"]

            if page_amount <= 50:
                ids.extend(get_pages(page_amount, kw_year))
            else:
                # 进一步细分查询
                num = 0
                ids_year = list()
                while len(ids_year) < total_amount:
                    kw_num = kw_year + "{:0>2}".format(num)
                    pages = get_pages_status(kw_num)["page_count"]
                    ids_year.extend(get_pages(pages, kw_num))
                    num += 1
```

### 2.2 分省查询策略

```python
cities = ["京", "津", "冀", "晋", "内", "辽", "吉", "黑", "沪", "苏", "浙", "皖", "闽", "赣", "鲁", "豫", "鄂", "湘", "粤", "桂", "琼", "川", "贵", "云", "渝", "藏", "陕", "甘", "青", "宁", "新"]
```

## 3. 反爬虫绕过技术

### 3.1 DrissionPage方案（Snoopy1866项目）

**技术特点：**
- 使用DrissionPage绕过Selenium检测
- 页面等待策略：等待10秒
- 适合需要渲染的页面

```python
# 伪代码示例
from DrissionPage import ChromiumPage

page = ChromiumPage()
page.get(url)
page.wait(10)  # 关键：等待10秒绕过检测
data = page.html
```

### 3.2 Magical Spider方案（lixi5338619项目）

**核心技术栈：**
- `undetected_selenium` + `stealth.min.js`
- Flask服务架构
- SQLite任务管理

**核心函数：**
```python
session_id, process_url = magical_start(project_name, base_url)
result = magical_request(session_id, process_url, target_url)
magical_close(session_id)
```

**适用场景：**
- 瑞数加密
- 加速乐加密
- 其他复杂加密场景

### 3.3 智能分页绕过（QueenOfBugs项目）

**核心技术：**
- 避免直接请求高页数
- 使用模糊查询：如`粤妆2016`
- 按年份细分
- 按编号进一步细分

## 4. 项目有效性评估

### 4.1 高度有效项目

**1. magical_spider（lixi5338619）**
- **成功率：★★★★★**
- **技术优势：**成熟的反检测技术，支持复杂加密
- **适用性：**适合各种加密场景
- **可直接使用：**是

**2. QueenOfBugs/scxk.nmpa**
- **成功率：★★★★☆**
- **技术优势：**完整的API调用方案，智能分页策略
- **适用性：**专门针对生产许可证数据
- **可直接使用：**是

**3. Billy-FIN/NMPA_Scraper**
- **成功率：★★★★☆**
- **技术优势：**JS逆向工程 + Requests
- **适用性：**多种技术方案备选
- **可直接使用：**部分可用

### 4.2 中等有效项目

**4. Snoopy1866/guidelines-crawler**
- **成功率：★★★☆☆**
- **技术优势：**DrissionPage方案
- **限制：**仅适用于指导原则页面

**5. bytesFighting/NMPA-spider**
- **成功率：★★★☆☆**
- **技术优势：**完整的数据解析流程
- **限制：**核心代码未完全公开

### 4.3 低有效项目

**6. nimua/NMPA_spider** - 代码未公开
**7. Oxford-NIL/NMPA-analysis** - 仅分析项目
**8. XGFan/nmpa** - Go语言实现，需要Chrome Driver
**9. shi-yuan/nmpa-data** - 项目不完整

## 5. 可直接使用的技术方案

### 5.1 方案一：签名算法 + API调用

```python
import requests
import hashlib
import json
from urllib.parse import quote

class NMPACrawler:
    def __init__(self):
        self.secret = "nmpasecret2020"
        self.headers = {
            'Origin': 'http://scxk.nmpa.gov.cn:81',
            'Referer': 'http://scxk.nmpa.gov.cn:81/xk/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        }
        self.list_url = "http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsList"
        self.detail_url = "http://scxk.nmpa.gov.cn:81/xk/itownet/portalAction.do?method=getXkzsById"

    def get_sign(self, params):
        """生成签名"""
        array = []
        for key in params:
            array.append(key + '=' + str(params[key]))

        # 参数排序
        param_str = '&'.join(sorted(array))

        # 添加密钥并编码
        ready_to_encode = param_str + "&" + self.secret
        encoded_str = quote(ready_to_encode)

        # MD5加密
        m = hashlib.md5()
        m.update(encoded_str.encode('utf-8'))
        return m.hexdigest()

    def get_list_data(self, page=1, page_size=15, keyword=""):
        """获取列表数据"""
        params = {
            'page': page,
            'pageSize': page_size,
            'productName': keyword,
            'sign': ''  # 这里需要根据实际参数生成签名
        }

        params['sign'] = self.get_sign(params)

        response = requests.post(self.list_url, data=params, headers=self.headers)
        return response.json()

    def get_detail_data(self, id):
        """获取详情数据"""
        params = {
            'id': id,
            'sign': ''
        }

        params['sign'] = self.get_sign(params)

        response = requests.post(self.detail_url, data=params, headers=self.headers)
        return response.json()
```

### 5.2 方案二：智能分页查询

```python
def smart_crawl_data(keyword=""):
    """智能查询策略"""
    cities = ["京", "津", "冀", "晋", "内", "辽", "吉", "黑", "沪", "苏", "浙", "皖", "闽", "赣", "鲁", "豫", "鄂", "湘", "粤", "桂", "琼", "川", "贵", "云", "渝", "藏", "陕", "甘", "青", "宁", "新"]

    all_data = []

    for city in cities:
        city_keyword = city + keyword
        try:
            # 获取该城市的数据
            city_data = crawl_city_data(city_keyword)
            all_data.extend(city_data)

            # 如果数据过多，按年细分
            if len(city_data) > 50:
                year_data = crawl_by_year(city_keyword)
                all_data.extend(year_data)

        except Exception as e:
            print(f"爬取{city}数据失败: {e}")
            continue

    return all_data

def crawl_by_year(base_keyword):
    """按年爬取数据"""
    year_data = []
    for year in range(2016, 2024):
        year_keyword = base_keyword + str(year)
        try:
            data = crawl_city_data(year_keyword)
            year_data.extend(data)
        except:
            continue
    return year_data
```

### 5.3 方案三：DrissionPage方案

```python
from DrissionPage import ChromiumPage
import time

def crawl_with_drissionpage(url):
    """使用DrissionPage爬取数据"""
    page = ChromiumPage()

    try:
        page.get(url)

        # 关键：等待10秒绕过检测
        time.sleep(10)

        # 获取页面数据
        html_content = page.html

        # 解析数据
        # ... 解析逻辑 ...

        return html_content

    except Exception as e:
        print(f"爬取失败: {e}")
        return None

    finally:
        page.quit()
```

## 6. 关键技术要点总结

### 6.1 签名算法要点
1. **密钥：** `nmpasecret2020`
2. **流程：** 参数排序 → 拼接 → 添加密钥 → URL编码 → MD5
3. **重要性：** 部分API需要签名验证

### 6.2 反爬虫要点
1. **页面等待：** 等待10秒可绕过部分检测
2. **分页策略：** 避免直接请求高页数，使用细分查询
3. **请求头：** 必须设置正确的Origin和Referer

### 6.3 API调用要点
1. **列表API：** `getXkzsList`
2. **详情API：** `getXkzsById`
3. **参数构造：** page, pageSize, productName等

## 7. 推荐使用方案

### 7.1 首选方案：magical_spider
- **理由：**最成熟，支持复杂加密
- **使用方法：**按照Flask服务架构部署
- **成功率：**最高

### 7.2 备选方案：API + 签名
- **理由：**直接调用API，效率高
- **使用方法：**实现签名算法，构造请求
- **成功率：**较高

### 7.3 兜底方案：DrissionPage
- **理由：**绕过浏览器检测
- **使用方法：**设置合适等待时间
- **成功率：**中等

## 8. 注意事项

1. **合规性：**请确保符合相关法律法规
2. **频率控制：**避免请求过于频繁
3. **数据准确性：**建议交叉验证数据
4. **技术更新：**反爬虫技术可能随时更新

## 9. 结论

通过分析9个NMPA爬虫项目，我们发现：

1. **最有效的技术**是magical_spider的undetected_selenium方案
2. **最实用的API方案**是QueenOfBugs的生产许可证爬虫
3. **签名算法**相对简单，关键是密钥`nmpasecret2020`
4. **反爬虫绕过**主要依靠等待时间和智能分页
5. **可以直接使用**的方案有2-3个，成功率较高

建议优先使用magical_spider方案，如果需要API调用则使用签名算法方案。