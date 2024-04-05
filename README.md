# HyperLane - Arbuzers 🍉

[![works on my machine badge](https://cdn.jsdelivr.net/gh/nikku/works-on-my-machine@v0.4.0/badge.svg)](https://github.com/nikku/works-on-my-machine)


### **Запускать на python 3.10!**

To run code:
```
python3.10 -m venv venv
```
```
source venv/bin/activate
```
```
pip install -r requirements.txt
```
```
python app.py
```


<br />

### **Выводы с биржи**:
Выводы если недостаточно денег на счету, для этого вам нужно:
- иметь баланс на правильной биржи и в правильной нативной монетке для контркетного блокчейна (например: Polygon - Matic)
- добавить api ключи для бирж в setings.json
- и указать True для нужных сетей в withdrawal_networks (setings.json)

*Раскидали монеты по биржам в зависимости от стоимости вывода.

_Если вы не хотите пользовать выводы с бирж и у вас уже есть балансы то ставим везде False в withdrawal_networks (setings.json)_

OKX:

    Polygon
    Base ETH
    Optimism ETH
    Moonbeam

Binance:

    Celo
    Avax
    BNB