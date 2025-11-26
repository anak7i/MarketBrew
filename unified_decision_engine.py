#!/usr/bin/env python3
"""
统一AI决策引擎 - 专注决策支持的分析系统
整合原有分析功能，专门为AI决策中心提供数据支持
"""

import os
import json
import glob
import time
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

class UnifiedDecisionEngine:
    def __init__(self):
        self.api_key = "sk-2700d9ebbb4c4374a8f697ae759d06fb"
        self.data_dir = "./data"
        self.results_dir = "./decision_data"
        self.price_service_url = "http://localhost:5002"  # 实时价格服务
        self.max_workers = 5
        self.batch_size = 50
        
        # 创建结果目录
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('decision_engine.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_all_stocks(self):
        """获取所有可分析的股票"""
        stock_files = glob.glob(os.path.join(self.data_dir, 'daily_prices_[0-9]*.json'))
        stocks = []
        
        for file_path in stock_files:
            filename = os.path.basename(file_path)
            symbol = filename.replace('daily_prices_', '').replace('.json', '')
            if len(symbol) == 6 and symbol.isdigit():  # 只处理A股代码
                stocks.append(symbol)
        
        stocks.sort()
        self.logger.info(f"📊 发现 {len(stocks)} 只A股待分析")
        return stocks
    
    def get_real_time_price(self, symbol):
        """获取实时价格数据"""
        try:
            response = requests.post(
                f"{self.price_service_url}/api/stocks",
                json={"symbols": [symbol]},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if symbol in data and not data[symbol].get('error'):
                    return data[symbol]
            return None
        except Exception as e:
            self.logger.warning(f"获取{symbol}实时价格失败: {e}")
            return None
    
    def analyze_single_stock(self, symbol):
        """分析单只股票，返回决策相关信息"""
        try:
            # 读取股票数据
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            if not os.path.exists(data_file):
                return None
            
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            # 获取股票名称
            stock_name = self.get_stock_name(symbol)
            
            # 处理价格数据
            time_series = stock_data.get('Time Series (Daily)', {})
            if not time_series:
                return None
            
            recent_dates = sorted(time_series.keys(), reverse=True)[:5]
            if len(recent_dates) < 3:
                return None
            
            latest_data = time_series[recent_dates[0]]
            
            # 优先使用实时价格和成交量数据
            real_time_data = self.get_real_time_price(symbol)
            if real_time_data and real_time_data.get('current_price'):
                current_price = float(real_time_data['current_price'])
                change_pct = float(real_time_data.get('change_percent', 0))
                current_volume = int(real_time_data.get('volume', 0))
                self.logger.info(f"📊 {symbol} 使用实时数据: ¥{current_price:.2f} ({change_pct:+.2f}%) 量:{current_volume:,}")
            else:
                # 回退到历史数据
                price_fields = ['4. close', '4. sell price']
                current_price = 0
                for field in price_fields:
                    if field in latest_data:
                        current_price = float(latest_data.get(field, 0))
                        break
                current_volume = int(latest_data.get('5. volume', 0))
                self.logger.info(f"📊 {symbol} 使用历史数据: ¥{current_price:.2f} 量:{current_volume:,}")
            
            # 增强数据验证 - 过滤异常价格和成交量数据
            if current_price <= 0.01:
                self.logger.warning(f"⚠️ {symbol} 价格数据异常(¥{current_price:.2f})，可能停牌或异常，跳过分析")
                return None
                
            if current_volume <= 0:
                self.logger.warning(f"⚠️ {symbol} 成交量数据异常({current_volume})，跳过分析")
                return None
            
            # 构建决策导向的分析提示词
            prompt = self.build_decision_prompt(symbol, stock_name, latest_data, recent_dates, time_series, current_price, change_pct, current_volume)
            
            # 调用AI分析
            analysis_result = self.call_deepseek_api(prompt)
            
            # 解析AI分析结果
            decision_data = self.parse_analysis_result(
                symbol, stock_name, latest_data, analysis_result, current_price, current_volume, change_pct
            )
            
            return decision_data
            
        except Exception as e:
            self.logger.error(f"❌ {symbol} 分析失败: {e}")
            return None
    
    def build_decision_prompt(self, symbol, name, latest_data, recent_dates, time_series, current_price, change_pct, current_volume):
        """构建专注决策的分析提示词"""
        
        # 计算平均成交量 - 使用历史数据作为基准
        avg_volume = sum([int(time_series[date].get('5. volume', 0)) for date in recent_dates[:3]]) // 3
        
        prompt = f"""
股票: {symbol} ({name})
价格: ¥{current_price:.2f} ({change_pct:+.1f}%)
成交量: {current_volume:,} (平均: {avg_volume:,})

请作为专业A股投资顾问，给出明确的投资决策建议：

1. 操作建议: [买入/卖出/持有] (必须明确选择一个)
2. 信号强度: [强烈/中等/较弱] 
3. 核心理由: (一句话说明主要判断依据)
4. 风险提示: (主要风险点)
5. 目标价位: (如适用)

要求：
- 决策明确，不模糊
- 理由简洁有力
- 考虑A股特点(T+1等)
- 突出实用性
"""
        return prompt
    
    def call_deepseek_api(self, prompt, retries=3):
        """调用DeepSeek API"""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是专业的A股投资决策顾问，专注于给出明确、实用的投资建议。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # 指数退避
    
    def parse_analysis_result(self, symbol, name, latest_data, analysis_text, current_price, current_volume, change_pct):
        """解析AI分析结果为标准化决策数据"""
        
        # 解析AI分析结果
        decision = "持有"  # 默认
        strength = "较弱"
        reason = "AI分析结果"
        risk_note = "注意市场风险"
        target_price = None
        
        # 使用正则表达式精确提取结构化信息
        import re
        
        # 1. 提取操作建议
        decision_pattern = r"操作建议[:：]\s*([买卖持][入出有])"
        decision_match = re.search(decision_pattern, analysis_text)
        if decision_match:
            action = decision_match.group(1)
            if action == "买入":
                decision = "买入"
            elif action == "卖出":
                decision = "卖出"
            elif action == "持有":
                decision = "持有"
        
        # 2. 提取信号强度
        strength_pattern = r"信号强度[:：]\s*([强中弱][烈等弱]|较弱|立即)"
        strength_match = re.search(strength_pattern, analysis_text)
        if strength_match:
            strength_text = strength_match.group(1)
            if strength_text == "强烈" or strength_text == "立即":
                strength = "强烈"
            elif strength_text == "中等":
                strength = "中等"
            else:
                strength = "较弱"
        
        # 3. 提取核心理由
        reason_pattern = r"核心理由[:：]\s*([^\n]+)"
        reason_match = re.search(reason_pattern, analysis_text)
        if reason_match:
            reason = reason_match.group(1).strip()
        
        # 4. 提取风险提示
        risk_pattern = r"风险提示[:：]\s*([^\n]+)"
        risk_match = re.search(risk_pattern, analysis_text)
        if risk_match:
            risk_note = risk_match.group(1).strip()
        
        # 5. 提取目标价位
        target_pattern = r"目标价位[:：]\s*([\d.]+)"
        target_match = re.search(target_pattern, analysis_text)
        if target_match:
            try:
                target_price = float(target_match.group(1))
            except:
                target_price = None
        
        return {
            "symbol": symbol,
            "name": name,
            "decision": decision,
            "strength": strength,
            "reason": reason,
            "risk_note": risk_note,
            "price": current_price,
            "volume": current_volume,
            "change_pct": change_pct,
            "target_price": target_price,
            "confidence": self.calculate_confidence(strength, decision),
            "timestamp": datetime.now().isoformat(),
            "full_analysis": analysis_text
        }
    
    def calculate_change_pct(self, symbol, current_price):
        """计算涨跌幅"""
        try:
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            time_series = stock_data.get('Time Series (Daily)', {})
            dates = sorted(time_series.keys(), reverse=True)
            
            if len(dates) >= 2:
                prev_data = time_series[dates[1]]
                # 支持不同价格字段
                price_fields = ['4. close', '4. sell price']
                prev_price = current_price
                for field in price_fields:
                    if field in prev_data:
                        prev_price = float(prev_data.get(field, current_price))
                        break
                        
                if prev_price > 0:
                    return round(((current_price - prev_price) / prev_price * 100), 2)
            return 0.0
        except:
            return 0.0
    
    def calculate_confidence(self, strength, decision):
        """计算决策置信度"""
        confidence_map = {
            ("强烈", "买入"): 0.9,
            ("强烈", "卖出"): 0.9,
            ("中等", "买入"): 0.7,
            ("中等", "卖出"): 0.7,
            ("较弱", "买入"): 0.5,
            ("较弱", "卖出"): 0.5,
            ("强烈", "持有"): 0.8,
            ("中等", "持有"): 0.6,
            ("较弱", "持有"): 0.4,
        }
        return confidence_map.get((strength, decision), 0.5)
    
    def get_stock_name(self, symbol):
        """获取股票名称 - 覆盖全部443只A股"""
        name_map = {
            '000001': '平安银行', '000002': '万科A', '000063': '中兴通讯', '000100': 'TCL科技',
            '000157': '中联重科', '000166': '申万宏源', '000301': '东方盛虹', '000333': '美的集团',
            '000338': '潍柴动力', '000423': '东阿阿胶', '000568': '泸州老窖', '000625': '长安汽车',
            '000651': '格力电器', '000683': '远兴能源', '000686': '东北证券', '000703': '恒逸石化',
            '000725': '京东方A', '000768': '中航西飞', '000776': '广发证券', '000783': '长江证券',
            '000792': '盐湖股份', '000839': '中信证券', '000858': '五粮液', '000876': '新希望',
            '000895': '双汇发展', '000898': '鞍钢股份', '000938': '紫光股份', '000961': '中南建设',
            '000977': '浪潮信息', '000983': '西山煤电', '002001': '新和成', '002008': '大族激光',
            '002024': '苏宁易购', '002027': '分众传媒', '002049': '紫光国微', '002065': '东华软件',
            '002081': '金螳螂', '002120': '韵达股份', '002129': '中环股份', '002142': '宁波银行',
            '002153': '石基信息', '002174': '游族网络', '002179': '中航光电', '002202': '金风科技',
            '002230': '科大讯飞', '002236': '大华股份', '002241': '歌尔股份', '002252': '上海莱士',
            '002271': '东方雨虹', '002304': '洋河股份', '002311': '海大集团', '002317': '众生药业',
            '002332': '仙琚制药', '002344': '海宁皮城', '002352': '顺丰控股', '002371': '北方华创',
            '002405': '四维图新', '002410': '广联达', '002415': '海康威视', '002422': '科伦药业',
            '002456': '欧菲光', '002460': '赣锋锂业', '002466': '天齐锂业', '002475': '立讯精密',
            '002493': '荣盛石化', '002507': '涪陵榨菜', '002555': '三七互娱', '002558': '巨人网络',
            '002572': '索菲亚', '002594': '比亚迪', '002601': '龙蟒佰利', '002602': '世纪华通',
            '002624': '完美世界', '002648': '卫星石化', '002673': '西部证券', '002709': '天赐材料',
            '002714': '牧原股份', '002736': '国信证券', '002739': '万达电影', '002756': '永兴材料',
            '002773': '康弘药业', '002821': '凯莱英', '002841': '视源股份', '002938': '鹏鼎控股',
            '002945': '华林证券', '002958': '青农商行',
            
            # 创业板股票 (300开头)
            '300001': '特锐德', '300002': '神州泰岳', '300003': '乐普医疗', '300004': '南风股份',
            '300005': '探路者', '300006': '莱美药业',
            '300007': '汉威科技', '300008': '天海防务', '300009': '安科生物', '300010': '立思辰',
            '300011': '鼎汉技术', '300012': '华测检测', '300013': '新宁物流', '300014': '亿纬锂能',
            '300015': '爱尔眼科', '300016': '北陆药业', '300017': '网宿科技', '300018': '中元股份',
            '300019': '硅宝科技', '300020': '银江股份', '300021': '大禹节水', '300022': '吉峰科技',
            '300023': '宝德股份', '300024': '机器人', '300025': '华星创业', '300026': '红日药业',
            '300027': '华谊兄弟', '300028': '金亚科技', '300029': '天龙光电', '300030': '阳普医疗',
            '300031': '宝通科技', '300032': '金龙机电', '300033': '同花顺', '300034': '钢研高纳',
            '300035': '中科电气', '300036': '超图软件', '300037': '新宙邦', '300038': '梅泰诺',
            '300039': '上海凯宝', '300040': '九洲药业', '300041': '回天新材', '300042': '朗科科技',
            '300043': '互动娱乐', '300044': '赛为智能', '300045': '华力创通', '300046': '台基股份',
            '300047': '天源迪科', '300048': '合康新能', '300049': '福瑞股份', '300050': '世纪鼎利',
            '300051': '三五互联', '300052': '中青宝', '300053': '欧比特', '300054': '鼎龙股份',
            '300055': '万邦达', '300056': '三维丝', '300057': '万顺股份', '300058': '蓝色光标',
            '300059': '东方财富', '300060': '福耀玻璃', '300061': '康耐特', '300062': '中能电气',
            '300063': '天龙集团', '300064': '豫金刚石', '300065': '海兰信', '300066': '三川智慧',
            '300067': '安诺其', '300068': '南都电源', '300069': '金利华电', '300070': '碧水源',
            '300071': '华谊嘉信', '300072': '三聚环保', '300073': '当升科技', '300074': '华平股份',
            '300075': '数字政通', '300076': 'GQY视讯', '300077': '国民技术', '300078': '思创医惠',
            '300079': '数码科技', '300080': '易成新能', '300081': '恒信东方', '300082': '奥克股份',
            '300083': '劲胜智能', '300084': '海默科技', '300085': '银之杰', '300086': '康芝药业',
            '300087': '荃银高科', '300088': '长信科技', '300089': '文化长城', '300090': '盛运环保',
            '300091': '金通灵', '300092': '科新机电', '300093': '金刚玻璃', '300094': '国联水务',
            '300095': '华伍股份', '300096': '易联众', '300097': '智云股份', '300098': '高新兴',
            '300099': '尤洛卡', '300122': '智飞生物', '300124': '汇川技术', '300136': '信维通信',
            '300142': '沃森生物', '300274': '阳光电源', '300308': '中际旭创', '300316': '晶盛机电',
            '300325': '德威新材', '300347': '泰格医药', '300357': '我武生物', '300363': '博腾股份',
            '300373': '扇贝科技', '300383': '光环新网', '300390': '天华超净', '300408': '三环集团',
            '300413': '芒果超媒', '300418': '昆仑万维', '300433': '蓝思科技', '300450': '先导智能',
            '300454': '深信服', '300482': '万孚生物', '300496': '中科创达', '300529': '健帆生物',
            '300558': '贝达药业', '300568': '星源材质', '300595': '欧普康视', '300601': '康泰生物',
            '300618': '寒锐钴业', '300628': '亿联网络', '300676': '华大基因', '300682': '朗新科技',
            '300699': '光威复材', '300724': '捷佳伟创', '300738': '奥飞数据', '300750': '宁德时代',
            '300751': '迈为股份', '300759': '康龙化成', '300760': '迈瑞医疗', '300772': '运达风电',
            '300782': '卓胜微', '300896': '爱美客', '300919': '中伟股份', '300957': '贝泰妮',
            '300979': '华利集团', '300999': '金龙鱼', '688001': '华兴源创', '688002': '睿创微纳',
            '688003': '天准科技', '688005': '容百科技', '688006': '杭可科技', '688007': '光峰科技',
            '688008': '澜起科技', '688009': '中国通号', '688010': '福光股份', '688011': '新光光电',
            '688012': '中微公司', '688013': '天臣医疗', '688015': '交控科技', '688016': '心脉医疗',
            '688017': '绿的谐波', '688018': '乐鑫科技', '688019': '安集科技', '688020': '方邦股份',
            '688021': '奥福环保', '688022': '瀚川智能', '688023': '安恒信息', '688025': '崧智股份',
            '688026': '洁特生物', '688027': '国盾量子', '688028': '沃尔德', '688029': '南微医学',
            '688030': '山石网科', '688031': '贝斯达', '688032': '禾迈股份', '688033': '天宜上佳',
            '688035': '德马科技', '688036': '传音控股', '688037': '芯源微', '688038': '赛特斯',
            '688039': '瀚川智能', '688041': '海光信息', '688045': '航天宏图', '688046': '药康生物',
            '688047': '龙芯中科', '688048': '长光华芯', '688049': '炬光科技', '688050': '爱博医疗',
            '688051': '佰仁医疗', '688052': '纳芯微', '688053': '金山办公', '688055': '龙腾光电',
            '688056': '莱伯泰科', '688057': '金现代', '688058': '宝兰德', '688059': '华锋股份',
            '688060': '云涌科技', '688061': '聚辰股份', '688062': '福昕软件', '688063': '派能科技',
            '688065': '凯赛生物', '688066': '航天发展', '688067': '爱威科技', '688068': '热景生物',
            '688069': '德林海', '688070': '纵横股份', '688071': '华大智造', '688072': '拓荆科技',
            '688073': '上海贝岭', '688075': '安旭生物', '688076': '诺泰生物', '688077': '大地熊',
            '688078': '龙软科技', '688079': '美迪西', '688080': '映翰通', '688081': '兴图新科',
            '688082': '盛美上海', '688083': '中望软件', '688085': '三友医疗', '688086': '紫光国微',
            '688087': '英科再生', '688088': '虹软科技', '688111': '金山办公', '688126': '沪硅产业',
            '688169': '石头科技', '688180': '君实生物', '688187': '时代电气', '688208': '道通科技',
            '688223': '晶科能源', '688256': '寒武纪', '688271': '联影医疗', '688290': '景业智能',
            '688303': '大全能源', '688363': '华熙生物', '688396': '华润微', '688561': '奇安信',
            '688599': '天合光能', '688981': '中芯国际', '689009': '九号公司', '600000': '浦发银行',
            '600004': '白云机场', '600009': '上海机场', '600010': '包钢股份', '600011': '华能国际',
            '600015': '华夏银行', '600016': '民生银行', '600018': '上港集团', '600019': '宝钢股份',
            '600025': '华能水电', '600028': '中国石化', '600029': '南方航空', '600030': '中信证券',
            '600031': '三一重工', '600035': '楚天高速', '600036': '招商银行', '600038': '中直股份',
            '600039': '四川路桥', '600048': '保利发展', '600050': '中国联通', '600058': '五矿发展',
            '600061': '国投资本', '600066': '宇通客车', '600068': '葛洲坝', '600085': '同仁堂',
            '600089': '特变电工', '600104': '上汽集团', '600110': '诺德股份', '600111': '北方稀土',
            '600115': '东方航空', '600150': '中国船舶', '600170': '上海建工', '600177': '雅戈尔',
            '600183': '生益科技', '600188': '兖州煤业', '600195': '中牧股份', '600196': '复星医药',
            '600208': '新湖中宝', '600216': '浙江医药', '600233': '圆通速递', '600256': '广汇能源',
            '600271': '航天信息', '600276': '恒瑞医药', '600309': '万华化学', '600362': '江西铜业',
            '600383': '金地集团', '600519': '贵州茅台', '600547': '山东黄金', '600585': '海螺水泥',
            '600588': '用友网络', '600690': '海尔智家', '600703': '三安光电', '600741': '华域汽车',
            '600745': '闻泰科技', '600809': '山西汾酒', '600837': '海通证券', '600887': '伊利股份',
            '600919': '江苏银行', '600958': '东方证券', '600968': '海油发展', '600999': '招商证券',
            '601006': '大秦铁路', '601012': '隆基绿能', '601066': '中信建投', '601088': '中国神华',
            '601138': '工业富联', '601166': '兴业银行', '601169': '北京银行', '601186': '中国铁建',
            '601211': '国泰君安', '601229': '上海银行', '601238': '广汽集团', '601288': '农业银行',
            '601318': '中国平安', '601328': '交通银行', '601336': '新华保险', '601360': '三六零',
            '601390': '中国中铁', '601398': '工商银行', '601601': '中国太保', '601628': '中国人寿',
            '601633': '长城汽车', '601688': '华泰证券', '601698': '中国卫通', '601728': '中国电信',
            '601766': '中国中车', '601788': '光大证券', '601799': '星宇股份', '601816': '京沪高铁',
            '601818': '光大银行', '601857': '中国石油', '601865': '福莱特', '601877': '正泰电器',
            '601878': '浙商证券', '601888': '中国中免', '601899': '紫金矿业', '601933': '永辉超市',
            '601939': '建设银行', '301015': '百洋医药', '301029': '怡合达', '301048': '金鹰重工',
            '301056': '森马服饰', '301076': '盛帮股份', '301087': '可孚医疗', '301111': '龙竹科技',
            '301138': '欧克科技', '301151': '冠盛股份', '301186': '汇绿生态', '301200': '大族数控',
            '301208': '优机股份', '301236': '软通动力', '301269': '华大九天', '301287': '建研设计',
            '301296': '超达装备', '301308': '江波龙', '301319': '唯特偶', '301326': '倍轻松',
            '301329': '海尔生物', '301339': '通行宝', '301348': '博汇科技'
        }
        return name_map.get(symbol, f'股票{symbol}')
    
    def run_full_analysis(self):
        """执行完整的决策分析"""
        start_time = datetime.now()
        self.logger.info(f"🚀 开始执行决策分析 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 获取所有股票
        all_stocks = self.get_all_stocks()
        if not all_stocks:
            self.logger.error("❌ 未找到股票数据")
            return None
        
        # 分批并发分析
        all_results = []
        batches = [all_stocks[i:i + self.batch_size] for i in range(0, len(all_stocks), self.batch_size)]
        
        for batch_num, batch in enumerate(batches, 1):
            self.logger.info(f"📊 分析第{batch_num}/{len(batches)}批 ({len(batch)}只)")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.analyze_single_stock, symbol) for symbol in batch]
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        all_results.append(result)
            
            # 批次间休息
            if batch_num < len(batches):
                time.sleep(10)
        
        # 生成决策数据
        decision_data = self.generate_decision_data(all_results)
        
        # 保存结果
        self.save_decision_data(decision_data)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        self.logger.info(f"✅ 决策分析完成!")
        self.logger.info(f"📊 分析股票: {len(all_results)}/{len(all_stocks)}")
        self.logger.info(f"⏱️ 耗时: {duration}")
        
        return decision_data
    
    def generate_decision_data(self, results):
        """生成决策数据摘要"""
        
        # 二次过滤 - 确保没有异常价格数据进入最终结果
        filtered_results = []
        for result in results:
            if result.get('price', 0) > 0.01:  # 再次验证价格
                filtered_results.append(result)
            else:
                self.logger.warning(f"⚠️ 最终过滤: {result.get('symbol')} 价格异常 ¥{result.get('price', 0):.2f}")
        
        # 按决策分类
        buy_stocks = [r for r in filtered_results if r['decision'] == '买入']
        sell_stocks = [r for r in filtered_results if r['decision'] == '卖出']
        hold_stocks = [r for r in filtered_results if r['decision'] == '持有']
        
        # 按置信度排序
        buy_stocks.sort(key=lambda x: x['confidence'], reverse=True)
        sell_stocks.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 生成市场分析
        market_analysis = self.generate_market_analysis(buy_stocks, sell_stocks, hold_stocks)
        
        decision_data = {
            "analysis_date": datetime.now().strftime('%Y-%m-%d'),
            "analysis_time": datetime.now().isoformat(),
            "total_stocks": len(filtered_results),
            "summary": {
                "buy_count": len(buy_stocks),
                "sell_count": len(sell_stocks),
                "hold_count": len(hold_stocks),
                "market_analysis": market_analysis,
                "risk_level": self.assess_market_risk(buy_stocks, sell_stocks)
            },
            "decisions": {
                "buy": buy_stocks[:20],  # 前20只买入推荐
                "sell": sell_stocks[:10],  # 前10只卖出建议
                "hold": hold_stocks[:10]   # 部分持有股票
            },
            "full_results": filtered_results
        }
        
        return decision_data
    
    def generate_market_analysis(self, buy_stocks, sell_stocks, hold_stocks):
        """生成市场分析"""
        total = len(buy_stocks) + len(sell_stocks) + len(hold_stocks)
        buy_ratio = len(buy_stocks) / total if total > 0 else 0
        
        if buy_ratio > 0.1:
            return "市场出现较多投资机会，建议积极关注优质个股，适当增加仓位。"
        elif buy_ratio > 0.05:
            return "市场呈现结构性行情，选股比选时更重要，重点关注有明确催化剂的个股。"
        else:
            return "市场整体偏谨慎，建议以观望为主，严格控制风险，等待更好时机。"
    
    def assess_market_risk(self, buy_stocks, sell_stocks):
        """评估市场风险等级"""
        total_signals = len(buy_stocks) + len(sell_stocks)
        
        if len(sell_stocks) > len(buy_stocks) * 1.5:
            return "较高"
        elif total_signals < 20:
            return "中等"
        else:
            return "适中"
    
    def save_decision_data(self, decision_data):
        """保存决策数据"""
        date_str = decision_data["analysis_date"]
        
        # 保存详细决策数据
        detailed_file = os.path.join(self.results_dir, f"decision_data_{date_str}.json")
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(decision_data, f, ensure_ascii=False, indent=2)
        
        # 保存最新决策数据
        latest_file = os.path.join(self.results_dir, "latest_decision.json")
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(decision_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 决策数据已保存: {detailed_file}")
    
    def get_latest_decisions(self):
        """获取最新决策数据"""
        latest_file = os.path.join(self.results_dir, "latest_decision.json")
        
        if os.path.exists(latest_file):
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_analysis_status(self):
        """获取分析状态"""
        latest_data = self.get_latest_decisions()
        
        if latest_data:
            analysis_time = datetime.fromisoformat(latest_data['analysis_time'])
            is_today = analysis_time.date() == datetime.now().date()
            
            return {
                "last_analysis": analysis_time.strftime('%Y-%m-%d %H:%M'),
                "is_today": is_today,
                "stock_count": latest_data['total_stocks'],
                "buy_signals": latest_data['summary']['buy_count'],
                "sell_signals": latest_data['summary']['sell_count'],
                "hold_signals": latest_data['summary']['hold_count'],
                "market_analysis": latest_data['summary']['market_analysis'],
                "risk_level": latest_data['summary']['risk_level']
            }
        
        return {
            "last_analysis": "未执行",
            "is_today": False,
            "stock_count": 0,
            "buy_signals": 0,
            "sell_signals": 0,
            "hold_signals": 0,
            "market_analysis": "等待分析...",
            "risk_level": "未知"
        }

def main():
    """主函数"""
    engine = UnifiedDecisionEngine()
    
    print("🤖 DeepSeek统一决策引擎")
    print("=" * 50)
    print("1. 执行完整决策分析")
    print("2. 查看最新决策数据")
    print("3. 查看系统状态")
    
    choice = input("\n请选择操作 (1-3): ").strip()
    
    if choice == "1":
        engine.run_full_analysis()
    elif choice == "2":
        latest = engine.get_latest_decisions()
        if latest:
            print(f"\n📊 最新决策数据 ({latest['analysis_date']}):")
            print(f"买入推荐: {latest['summary']['buy_count']}只")
            print(f"卖出建议: {latest['summary']['sell_count']}只")
            print(f"持有观望: {latest['summary']['hold_count']}只")
            print(f"市场分析: {latest['summary']['market_analysis']}")
        else:
            print("❌ 暂无决策数据")
    elif choice == "3":
        status = engine.get_analysis_status()
        print(f"\n📈 系统状态:")
        for key, value in status.items():
            print(f"{key}: {value}")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()