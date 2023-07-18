# quant

### 更新数据

```bash
python cron/update_stock_by_qstock.py
```

### 跑回测

```bash
python run.py 
```

## 策略

### MyStrategy01

30天内涨幅超过20%，并且10天内价格处于均线（上下3%）箱体中，发出买入信号

### StrategyBigSmallRotate

https://mp.weixin.qq.com/s/g8TyAWZABtOc8Ir6vWe18Q

https://mp.weixin.qq.com/s/80-JLBWLrzJQinmLDqqkyA

大小盘轮动策略

### MomentumStrategy
动量轮动策略
https://mp.weixin.qq.com/s/2pl_Vv64yoI5GhPyN1t4Aw
```bash
python momentum.py
```


