"""Genera manuales HTML imprimibles desde Markdown, sin dependencias externas."""
from pathlib import Path
import re,html,unicodedata
ROOT=Path(__file__).resolve().parents[1]
CSS='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font:16px/1.75 "Segoe UI",Arial,sans-serif;color:#19374a;background:#f3f7f8}header{background:#123d5a;color:white;padding:32px max(24px,calc((100vw - 1120px)/2));border-bottom:5px solid #21b6b2}header p{margin:0;font-size:12px;letter-spacing:1.4px;text-transform:uppercase}header b{font-size:24px;display:block;margin-top:5px}nav.tabs{background:white;border-bottom:1px solid #dce7ec;display:flex;gap:25px;padding:16px max(24px,calc((100vw - 1120px)/2));flex-wrap:wrap}a{color:#147fae;text-underline-offset:3px}.tabs a{font-size:13px;font-weight:600;text-decoration:none}.layout{max-width:1168px;margin:32px auto;display:grid;grid-template-columns:220px minmax(0,1fr);gap:30px;padding:0 24px}.toc{align-self:start;position:sticky;top:25px;font-size:12px;line-height:1.5}.toc b{display:block;margin-bottom:15px;text-transform:uppercase;font-size:10px;letter-spacing:1px;color:#16877f}.toc a{display:block;text-decoration:none;color:#526d7d;padding:6px 0}.paper{background:white;border:1px solid #dce7ec;border-radius:12px;padding:40px;min-width:0}h1{font-size:34px;line-height:1.2;letter-spacing:-.7px;color:#123d5a;margin-top:0}h2{font-size:23px;line-height:1.3;color:#123d5a;margin-top:38px;scroll-margin-top:25px}p{margin:14px 0}li{margin:9px 0}table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.6;margin:22px 0}th,td{padding:12px 14px;border:1px solid #d8e3e7;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#e7f2f6;color:#173e55}tr:nth-child(even) td{background:#f8fafb}pre{padding:20px;background:#f1f5f7;border-radius:8px;overflow:auto;font-size:13px;line-height:1.7;white-space:pre-wrap;overflow-wrap:anywhere}code{font-family:Consolas,monospace;font-size:.9em}footer{max-width:1120px;margin:30px auto;padding:25px;border-top:1px solid #dce7ec;font-size:12px;color:#637e8a}@media(max-width:800px){.layout{display:block;padding:0 14px}.toc{position:static;margin-bottom:25px}.paper{padding:25px}h1{font-size:28px}table{font-size:11px}th,td{padding:8px}.tabs{gap:12px!important}}@media print{body{background:white;font-size:11pt;line-height:1.55}header,.tabs,.toc,footer{display:none!important}.layout{display:block;margin:0;padding:0}.paper{border:0;padding:0}h1,h2{color:black}h1{font-size:22pt}h2{font-size:15pt;break-after:avoid}p,li{orphans:3;widows:3}table{font-size:9pt}tr{break-inside:avoid}pre{font-size:9pt}@page{margin:20mm}}'''
def inline(text):
    text=html.escape(text).replace('\\|','|')
    text=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
    text=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'<a href="\2">\1</a>',text)
    return text
def slug(s):return re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip('-')
def render(text):
    lines=text.splitlines();out=[];toc=[];i=0
    while i<len(lines):
        line=lines[i]
        if not line.strip():i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
            out.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>');i+=1;continue
        if line.startswith('#'):
            n=len(line)-len(line.lstrip('#'));title=line[n:].strip();anchor=slug(title);out.append(f'<h{n} id="{anchor}">{inline(title)}</h{n}>')
            if n==2:toc.append((anchor,title))
            i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                row=re.split(r'(?<!\\)\|',lines[i].strip().strip('|'));rows.append([x.strip() for x in row]);i+=1
            out.append('<div class="table"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
            for row in rows[2:]:out.append('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>')
            out.append('</tbody></table></div>');continue
        if re.match(r'^(\d+\. |\- )',line):
            ordered=line[0].isdigit();tag='ol' if ordered else 'ul';out.append('<'+tag+'>')
            while i<len(lines) and re.match(r'^(\d+\. |\- )',lines[i]):out.append('<li>'+inline(re.sub(r'^(\d+\. |\- )','',lines[i]))+'</li>');i+=1
            out.append('</'+tag+'>');continue
        para=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|\d+\. |\- )',lines[i]):para.append(lines[i]);i+=1
        out.append('<p>'+inline(' '.join(para))+'</p>')
    return '\n'.join(out),toc
names={'usuario':'Usuario','sistema':'Sistema','datos':'Datos','alcance':'Alcance y verificación'}
for key,label in names.items():
    source=(ROOT/'manuales'/f'{key}.md').read_text('utf-8');body,toc=render(source);title=source.splitlines()[0].lstrip('# ')
    page='<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+' · IETS</title><style>'+CSS+'</style></head><body><header><p>Observatorio IETS · Colombia · Prototipo local 1.0.0</p><b>Georreferenciación para la acción</b></header><nav class="tabs" aria-label="Manuales">'+''.join('<a href="'+k+'.html">'+v+'</a>' for k,v in names.items())+'<a href="../app/index.html">Abrir aplicación ↗</a></nav><div class="layout"><aside class="toc"><b>En este manual</b>'+''.join('<a href="#'+a+'">'+html.escape(t)+'</a>' for a,t in toc)+'</aside><main class="paper">'+body+'</main></div><footer>Observatorio IETS · Documentación de transferencia · 30 de octubre de 2026 · Puede imprimir este manual desde el navegador.</footer></body></html>'
    (ROOT/'manuales'/f'{key}.html').write_text(page,'utf-8')
print('Manuales HTML generados:',len(names))
