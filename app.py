<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ lg.n }}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0e1a2f;color:#cbd5e1;font-family:Inter,sans-serif;font-size:14px}
.top{background:#132040;padding:12px 14px;border-bottom:1px solid #1e3354}
.back{color:#22c55e;text-decoration:none;font-size:13px;font-weight:700}
.title{font-size:18px;font-weight:800;color:#fff;margin-top:8px}
.subtitle{font-size:11px;color:#8da0bf;margin-top:4px}
.row{display:flex;justify-content:space-between;padding:14px;background:#1a2c4a;border-bottom:1px solid #1e3354;color:#fff;text-decoration:none}
.time{color:#8da0bf;font-size:13px}
.sec{background:#0c1830;padding:8px 14px;font-weight:800;color:#fff;font-size:11px;border-bottom:1px solid #1e3354}
</style>
</head>
<body>
<div class="top">
<a href="/" class="back">← Back</a>
<div class="title">{{ lg.n.replace('Spain - Spain - ','').replace('England - England - ','').replace(' - - ',' - ') }}</div>
<div class="subtitle">{{ lg.n }} • All fixtures</div>
</div>
<div class="sec">MATCHES</div>
{% if games %}
  {% for g in games %}
    <a class="row" href="/game/{{ g.id if g.id is defined else g }}"><span>{{ g.home if g.home is defined else g }}</span><span class="time">{{ g.time if g.time is defined else '' }} ›</span></a>
  {% endfor %}
{% else %}
  <div style="padding:30px;text-align:center;color:#8da0bf">No fixtures found for {{ lg.n }} - Check app.py league filter</div>
{% endif %}
</body>
</html>
