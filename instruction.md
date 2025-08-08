我要设计一个Portfolio Tracker，或者叫做Asset Managerment System。这个系统需要跟踪管理我的所有资产，包括股票，基金，债券，银行存款等。

# 设计原则
- 部署在本地，个人使用
- 操作系统是Windows或Mac OS
- 使用Vue + FastAPI + SQLModel+ SQLite
- 项目结构应减少前后端的耦合，前端只负责界面和展示，后端只负责业务逻辑和计算


# 外汇和币种
- 支持多币种，包括人民币，美元，港币等
- 系统可设置**主币种**，主币种默认为人民币
- 不同币种的现金和资产，根据不同外汇汇率，自动转换为**主币种**
- 现金和资产可选择显示为**主币种**或**原币种**
- 用户设置和更新不同币种的兑换汇率（可通过csv文件导入）

# 公司行动和利息
- 用户可设置单只股票的分红税率，系统在处理`dividends`交易时自动扣税
- 对于债券和银行存款，用户可设置计息要素，系统可自动生成`interest`交易流水

# 实时价格和历史价格
- 每个交易日日间，系统通过AKShare或其他API获取各项资产的实时价格，如果获取不了，则停留在上一个实时价格或历史价格
- 用户上传各项资产的历史价格（csv文件），系统根据CSV文件获取各项资产的历史价格

# Metadata
The system can associate metadata to any position. This is done via the meta section.

Each metadata entry consists of a match section (similar to the one used for prices) which can match a position by its symbol(ticker), and an apply section containing a list of attributes and values. Let's look at an example:
```
meta:
  - match:
      symbol: 600036.SH                       # Match position by its ticker
    apply:
      sector: Communication Services   # Set attribute "sector" to "Communication Services"
```
Here we are saying that the sector of our position with ticker FB is "Communication Services". Notice that instead of sector we could have put anything!

## Multiple values
Sometime a position may extend over multiple sectors, this is common for mutual funds, ETFs, etc. Inverno let's you specify multiple values for an attribute:
```
meta:
  - match:
      name: My Fund
    apply:
      sector:
          Information Technology: 50%
          Communication Services: 30%
```
Here we are saying that the sector of My Fund is 50% Information Technology, 30% Communication Services and 20% unknown.

# 交易流水
用户可以通过系统界面输入交易流水，也可以通过csv文件导入交易流水。

The transactions file will have the following columns:
trade_date: date the transaction happened (e.g. 2025-06-25)
action: type of transaction, available types are:
- buy: for purchases of new positions (e.g. buying stock)
- sell: for selling positions (e.g. selling stock)
- cash_in: for cash flowing in (e.g. cash deposit, salary, etc.)
- cash_out: for cash flowing out (e.g. withdrowal)
- tax: for any sort of tax payment associated to the investment account
- dividends: for dividends payed by a position. This increases the cash balance.
- split: for stock split events. This can also be used for bonus shares (`送股`). The `quantity` field should represent the split ratio (e.g., 2 for a 2-for-1 split).
- interest: for interest received from cash, bonds, or other assets.
symbol: ticker of the position, if applicable (e.g. GOOGL, FB, etc.)
name: (optional) name of the position, can be anything (e.g. Google, Facebook, MyFund, etc.)
isin: (optional) ISIN of the position, if applicable (e.g. US38259P7069)
quantity: (needed for buy/sell/vest transactions) number of positions purchased/sold/vested (e.g. 3.5)
price: (either price or amount are needed for buy/sell transactions) position price at the moment of the purchase/sale, corresponds to the price multiplied by the quantity (e.g. $102.2)
amount: (either price or amount are needed for buy/sell transactions) total cash amount of the transaction price at the moment of the purchase/sale, corresponds to the price multiplied by the quantity (e.g. $424.2)
fees: (optional) transaction costs (e.g. $2.4)

# 统计
- 系统使用基金净值算法（即计算Time Weighted Return），计算整个账户的净值。
- 统计账户的净值，绘制净值曲线，与市场基准做对比
- 统计账户和各项资产的收益率、最大回撤、夏普比率等指标
- 统计各行业、各资产的占比
- 各种统计应美观地展示给用户

# Time Weighted Return (TWR) 算法
## 1. 初始化参数（每日开始时）
- **前一日组合总净值（$V_{prev}$）**：昨日收盘组合总价值。
- **前一日总份额（$Shares_{prev}$）**：昨日收盘后总份额数。
- **当日组合总净值（$V_{today}$）**：当日收盘组合总价值。
- **当日现金流记录**：明确申购（流入，正值）和赎回（流出，负值）金额。
## 2. 处理外部现金流
**外部净现金流**：  
  $$ \Delta CF = 申购总额 + 赎回总额 $$
  赎回总额为负值，例如投资者赎回50万，则 CF = 100万（申购） + (-50万) = 50万净流入
## 3. 计算当日收益率
基金净值算法无需这一步，这里只是为了演示`每日时间加权法和基金净值法是等价的`。
**当日收益率公式**：  
  $$ r = \frac{(V_{today} - \Delta CF)}{V_{prev}} - 1 $$
  说明：
  - $V_{prev}$：前一日组合总净值。
  - $\Delta CF$：当日外部净现金流（申购总额 + 赎回总额）。
  - $V_{today}$：当日组合总净值。
## 4. 计算当日每份净值
- **前一日每份净值**：  
   $$ NAV_{prev} = \frac{V_{prev}}{Shares_{prev}} $$
- **当日每份净值**：  
   $$
   NAV_{today} = \frac{V_{today}}{Shares_{prev}} 
    = NAV_{prev} \times (1 + r)
   $$
## 5. 处理份额变动
- **申购新增份额**：  
  $$ Shares_{new} = \frac{申购金额}{NAV_{today}} $$
- **赎回减少份额**：  
  $$ Shares_{redeemed} = \frac{|赎回金额|}{NAV_{today}} $$
- **当日总份额**：  
  $$ Shares_{today} = Shares_{prev} + Shares_{new} - Shares_{redeemed} $$
## 6. 更新组合状态（为次日计算做准备）
- $V_{prev} = V_{today}$（重置上一日组合净值）
- $Shares_{prev} = Shares_{today}$（重置上一日份额）
