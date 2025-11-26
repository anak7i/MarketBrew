#!/usr/bin/env python3
"""
股票订阅管理系统
负责订阅数据管理、推送消息生成和历史记录
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from unified_decision_engine import UnifiedDecisionEngine

class StockSubscriptionManager:
    def __init__(self):
        self.subscriptions_file = "./subscription_data/subscriptions.json"
        self.history_file = "./subscription_data/push_history.json"
        self.subscription_dir = "./subscription_data"
        
        # 创建数据目录
        if not os.path.exists(self.subscription_dir):
            os.makedirs(self.subscription_dir)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('subscription.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化决策引擎
        self.decision_engine = UnifiedDecisionEngine()
        
        # 加载数据
        self.subscriptions = self.load_subscriptions()
        self.push_history = self.load_push_history()
    
    def load_subscriptions(self) -> List[Dict]:
        """加载订阅列表"""
        if os.path.exists(self.subscriptions_file):
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_subscriptions(self):
        """保存订阅列表"""
        with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
            json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
    
    def load_push_history(self) -> List[Dict]:
        """加载推送历史"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_push_history(self):
        """保存推送历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.push_history, f, ensure_ascii=False, indent=2)
    
    def add_subscription(self, symbol: str, name: str = None) -> bool:
        """添加股票订阅"""
        try:
            # 检查是否已存在
            if any(sub['symbol'] == symbol for sub in self.subscriptions):
                self.logger.warning(f"股票 {symbol} 已在订阅列表中")
                return False
            
            # 获取股票名称
            if not name:
                name = self.decision_engine.get_stock_name(symbol)
            
            subscription = {
                "symbol": symbol,
                "name": name,
                "added_at": datetime.now().isoformat(),
                "active": True
            }
            
            self.subscriptions.append(subscription)
            self.save_subscriptions()
            
            self.logger.info(f"✅ 添加订阅: {symbol} {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 添加订阅失败: {e}")
            return False
    
    def remove_subscription(self, symbol: str) -> bool:
        """移除股票订阅"""
        try:
            original_length = len(self.subscriptions)
            self.subscriptions = [sub for sub in self.subscriptions if sub['symbol'] != symbol]
            
            if len(self.subscriptions) < original_length:
                self.save_subscriptions()
                self.logger.info(f"🗑️ 移除订阅: {symbol}")
                return True
            else:
                self.logger.warning(f"未找到订阅股票: {symbol}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 移除订阅失败: {e}")
            return False
    
    def get_subscriptions(self) -> List[Dict]:
        """获取所有订阅"""
        return [sub for sub in self.subscriptions if sub.get('active', True)]
    
    def toggle_subscription(self, symbol: str) -> bool:
        """切换订阅状态"""
        for sub in self.subscriptions:
            if sub['symbol'] == symbol:
                sub['active'] = not sub.get('active', True)
                self.save_subscriptions()
                status = "激活" if sub['active'] else "暂停"
                self.logger.info(f"🔄 {status}订阅: {symbol}")
                return True
        return False
    
    def analyze_subscription(self, symbol: str) -> Optional[Dict]:
        """分析单只订阅股票"""
        try:
            # 使用决策引擎分析股票
            result = self.decision_engine.analyze_single_stock(symbol)
            
            if not result:
                self.logger.warning(f"⚠️ 无法获取 {symbol} 的分析数据")
                return None
            
            # 生成推送消息
            push_message = self.generate_push_message(result)
            
            return push_message
            
        except Exception as e:
            self.logger.error(f"❌ 分析股票 {symbol} 失败: {e}")
            return None
    
    def generate_push_message(self, analysis: Dict) -> Dict:
        """生成推送消息"""
        symbol = analysis['symbol']
        name = analysis['name']
        price = analysis['price']
        decision = analysis['decision']
        strength = analysis['strength']
        reason = analysis['reason']
        risk_note = analysis.get('risk_note', '')
        change_pct = analysis.get('change_pct', 0)
        volume = analysis.get('volume', 0)
        
        # 生成价格变化提示
        price_change_text = ""
        if change_pct > 0:
            price_change_text = f"📈 上涨 {change_pct:.2f}%"
        elif change_pct < 0:
            price_change_text = f"📉 下跌 {abs(change_pct):.2f}%"
        else:
            price_change_text = "➡️ 平盘"
        
        # 根据决策生成操作建议
        action_emoji = {
            "买入": "🟢",
            "卖出": "🔴", 
            "持有": "🟡"
        }.get(decision, "⚪")
        
        # 强度提示
        strength_text = {
            "强烈": "💪",
            "中等": "👍",
            "较弱": "👌"
        }.get(strength, "")
        
        # 构建推送消息
        title = f"{action_emoji} {symbol} {name}"
        
        content = f"""
💰 当前价格: ¥{price:.2f} {price_change_text}
📊 成交量: {volume:,}
🎯 操作建议: {decision} {strength_text}
📝 分析理由: {reason}
"""
        
        if risk_note:
            content += f"⚠️ 风险提示: {risk_note}\n"
        
        # 添加时间戳和技术指标
        content += f"""
⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🔍 信号强度: {strength}
"""
        
        push_data = {
            "symbol": symbol,
            "name": name,
            "title": title,
            "content": content.strip(),
            "price": price,
            "decision": decision,
            "strength": strength,
            "reason": reason,
            "risk_note": risk_note,
            "change_pct": change_pct,
            "volume": volume,
            "timestamp": datetime.now().isoformat(),
            "push_type": "daily_analysis"
        }
        
        return push_data
    
    def send_push_notification(self, push_data: Dict) -> bool:
        """发送推送通知"""
        try:
            # 记录推送历史
            self.push_history.append(push_data)
            self.save_push_history()
            
            # 这里可以集成实际的推送服务
            # 比如：邮件、微信、短信等
            self.logger.info(f"📤 推送通知: {push_data['symbol']} {push_data['name']}")
            self.logger.info(f"💬 内容: {push_data['title']}")
            
            # 模拟推送成功
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 推送失败: {e}")
            return False
    
    def daily_analysis_and_push(self) -> Dict:
        """执行每日分析和推送"""
        start_time = datetime.now()
        self.logger.info(f"🚀 开始每日订阅股票分析 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        active_subscriptions = self.get_subscriptions()
        if not active_subscriptions:
            self.logger.warning("📭 没有活跃的订阅股票")
            return {
                "success": True,
                "message": "没有活跃的订阅股票",
                "total": 0,
                "pushed": 0
            }
        
        pushed_count = 0
        failed_count = 0
        
        for subscription in active_subscriptions:
            symbol = subscription['symbol']
            self.logger.info(f"📊 分析股票: {symbol}")
            
            try:
                # 分析股票
                analysis = self.analyze_subscription(symbol)
                
                if analysis:
                    # 发送推送
                    if self.send_push_notification(analysis):
                        pushed_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                self.logger.error(f"❌ 处理股票 {symbol} 时出错: {e}")
                failed_count += 1
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        result = {
            "success": True,
            "message": f"每日推送完成",
            "total": len(active_subscriptions),
            "pushed": pushed_count,
            "failed": failed_count,
            "duration": str(duration),
            "timestamp": end_time.isoformat()
        }
        
        self.logger.info(f"✅ 每日推送完成: 成功{pushed_count}，失败{failed_count}，耗时{duration}")
        return result
    
    def get_push_history(self, days: int = 7) -> List[Dict]:
        """获取推送历史"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered_history = [
            push for push in self.push_history
            if datetime.fromisoformat(push['timestamp']) > cutoff_date
        ]
        
        return sorted(filtered_history, key=lambda x: x['timestamp'], reverse=True)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        today = datetime.now().date()
        
        # 今日推送统计
        today_pushes = [
            push for push in self.push_history
            if datetime.fromisoformat(push['timestamp']).date() == today
        ]
        
        # 本周推送统计
        week_start = today - timedelta(days=today.weekday())
        week_pushes = [
            push for push in self.push_history
            if datetime.fromisoformat(push['timestamp']).date() >= week_start
        ]
        
        return {
            "total_subscriptions": len(self.subscriptions),
            "active_subscriptions": len(self.get_subscriptions()),
            "total_pushes": len(self.push_history),
            "today_pushes": len(today_pushes),
            "week_pushes": len(week_pushes),
            "last_push": self.push_history[-1]['timestamp'] if self.push_history else None
        }
    
    def cleanup_old_history(self, days: int = 30):
        """清理旧的推送历史"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        original_count = len(self.push_history)
        self.push_history = [
            push for push in self.push_history
            if datetime.fromisoformat(push['timestamp']) > cutoff_date
        ]
        
        cleaned_count = original_count - len(self.push_history)
        
        if cleaned_count > 0:
            self.save_push_history()
            self.logger.info(f"🧹 清理了 {cleaned_count} 条旧推送记录")
        
        return cleaned_count

if __name__ == "__main__":
    # 测试订阅管理器
    manager = StockSubscriptionManager()
    
    # 添加测试订阅
    test_stocks = [
        ("000001", "平安银行"),
        ("000858", "五粮液"),
        ("600519", "贵州茅台")
    ]
    
    print("📋 添加测试订阅...")
    for symbol, name in test_stocks:
        manager.add_subscription(symbol, name)
    
    print(f"\n📊 当前订阅: {len(manager.get_subscriptions())} 只")
    
    print("\n🧪 执行测试推送...")
    result = manager.daily_analysis_and_push()
    print(f"推送结果: {result}")
    
    print("\n📈 统计信息:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")