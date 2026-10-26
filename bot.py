import os, json, math, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

API='https://biquote.io/api/XAUUSD/ohlc'
STATE=Path('state.json')
SESSION=requests.Session()

def ema(values, n):
    a=2/(n+1); x=values[0]
    for v in values[1:]: x=a*v+(1-a)*x
    return x

def atr(bars, n=14):
    trs=[]
    for i in range(1,len(bars)):
        p=bars[i-1]['close']; b=bars[i]
        trs.append(max(b['high']-b['low'],abs(b['high']-p),abs(b['low']-p)))
    if len(trs)<n: raise ValueError('Not enough bars for ATR')
    x=sum(trs[:n])/n
    for tr in trs[n:]: x=(x*(n-1)+tr)/n
    return x

def telegram(msg):
    token=os.environ.get('TELEGRAM_BOT_TOKEN'); chat=os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat: raise RuntimeError('Telegram secrets missing')
    r=SESSION.post(f'https://api.telegram.org/bot{token}/sendMessage',json={'chat_id':chat,'text':msg},timeout=20)
    r.raise_for_status()
    if not r.json().get('ok'): raise RuntimeError('Telegram returned not ok')

def get_bars():
    r=SESSION.get(API,params={'interval':'5m','limit':250},timeout=25)
    r.raise_for_status(); data=r.json()
    raw=data.get('bars',[])
    out=[]
    for b in raw:
        if b.get('isOpen') is True: continue
        try:
            t=datetime.fromisoformat(b['openTime'].replace('Z','+00:00'))
            out.append({'t':t,'open':float(b['open']),'high':float(b['high']),'low':float(b['low']),'close':float(b['close'])})
        except (ValueError,KeyError,TypeError): continue
    out.sort(key=lambda b:b['t'])
    out=[b for b in out if b['t']+timedelta(minutes=5)<=datetime.now(timezone.utc)]
    if len(out)<115: raise RuntimeError(f'Only {len(out)} closed bars; need >=115')
    if datetime.now(timezone.utc)-(out[-1]['t']+timedelta(minutes=5))>timedelta(minutes=15):
        raise RuntimeError('Market closed or candle data stale; no signal')
    return out

def main():
    bars=get_bars(); latest=bars[-1]; candle=latest['t'].isoformat()
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    # Do not backfill or send historical signals on first run.
    if not state.get('last_candle'):
        STATE.write_text(json.dumps({'last_candle':candle,'position':None,'entries':{},'bar_counter':0},indent=2)+'\n')
        print('Initialized without historical alert:',candle); return
    if candle<=state['last_candle']:
        print('No new candle:',candle); return
    # If GitHub schedule missed many bars, skip signal rather than pretend execution.
    previous=datetime.fromisoformat(state['last_candle'])
    if latest['t']-previous>timedelta(minutes=10):
        state['position']=None
        print('Missed bars: virtual position reset for safety')
    day=latest['t'].date().isoformat()
    entries=state.get('entries',{})
    entries={k:v for k,v in entries.items() if k>= (latest['t'].date()-timedelta(days=3)).isoformat()}
    position=state.get('position')
    if position:
        position['held']=position.get('held',0)+1
        side=position['side']; sl=position['sl']; tp=position['tp']
        # Conservative assumption: SL first when both touched in same bar.
        sl_hit=latest['low']<=sl if side=='BUY' else latest['high']>=sl
        tp_hit=latest['high']>=tp if side=='BUY' else latest['low']<=tp
        if sl_hit or tp_hit or position['held']>=24:
            reason='SL' if sl_hit else 'TP' if tp_hit else '24-bar time exit'
            print('Virtual position exited:',reason)
            position=None
    closes=[b['close'] for b in bars]
    trend=ema(closes,100)
    previous10=bars[-11:-1]
    side=('BUY' if latest['close']>trend and latest['close']>max(b['high'] for b in previous10)
          else 'SELL' if latest['close']<trend and latest['close']<min(b['low'] for b in previous10)
          else None)
    if not position and side and entries.get(day,0)<2:
        dist=atr(bars)*1.8
        # Estimate next-open entry using latest close; not a guaranteed execution price.
        entry=latest['close']; sign=1 if side=='BUY' else -1
        sl=entry-sign*dist; tp=entry+sign*dist*3
        message=(f'🟢 GOLD V9 {side}' if side=='BUY' else f'🔴 GOLD V9 {side}')
        message+=(f'\nXAUUSD M5 | {candle} UTC\nIndicative entry: {entry:.2f}'
                  f'\nSL: {sl:.2f}\nTP: {tp:.2f}'
                  '\nEMA100 + BOS10 | ATR(14) x1.8 | RR 1:3'
                  '\n⚠️ Biquote quotes, not XM. Demo signal; not an order.')
        telegram(message)
        position={'side':side,'entry':entry,'sl':sl,'tp':tp,'held':0}
        entries[day]=entries.get(day,0)+1
        print('Sent:',side,candle)
    state.update({'last_candle':candle,'position':position,'entries':entries})
    STATE.write_text(json.dumps(state,indent=2)+'\n')
    print('Processed',candle,'position',position and position['side'])

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        sys.exit(1)
