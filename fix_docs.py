import os
import re

replacements = {
    r'(?i)Web application for analytics support of Discord and Discourse community administrators': r'Web application for analytics support of Discord and Discourse community administrators',
    r'(?i)Asynchronous event processing using Python asyncio and Redis.': r'Asynchronous event processing using Python asyncio and Redis.',
    r'(?i)Asynchronous event processing using Python asyncio and Redis.': r'Asynchronous event processing using Python asyncio and Redis.',
    r'(?i)stored with a configurable retention (default 90 days)': r'stored with a configurable retention (default 90 days)',
    r'(?i)Výchozí retence hlavních detailních eventů je 90 dní a je konfigurovatelná.': r'Výchozí retence hlavních detailních eventů je 90 dní a je konfigurovatelná.',
    r'(?i)Metadata-only Aggregation': r'Metadata-only Aggregation',
    r'(?i)Minimalizace uživatelských dat': r'Minimalizace uživatelských dat',
    r'(?i)metadata-only': r'metadata-only',
    r'(?i)metadata-only storage': r'metadata-only storage',
    r'(?i)experimentální predikce': r'experimentální predikce',
    r'(?i)experimental prediction(s)?': r'experimental prediction',
    r'(?i)experimentální agregovaný indikátor': r'experimentální agregovaný indikátor',
    r'(?i)uživatel označený experimentálním indikátorem': r'uživatel označený experimentálním indikátorem',
    r'(?i)experimentální model ukazuje vyšší šanci na přechod do neaktivity': r'experimentální model ukazuje vyšší šanci na přechod do neaktivity',
    r'(?i)7 dní stačí na(.*?)experimentální predikce': r'7 dní může být použito pro základní trend, ale není dostatečné pro komplexní modely',
    r'(?i)Authorization:\s*Bearer\s+YOUR_TOKEN': r'X-API-Key: YOUR_API_KEY',
    r'(?i)60\s*requests/minute': r'120 requests/minute',
    r'(?i)signed session cookie': r'signed session cookie',
    r'(?i)podepsaná session cookie': r'podepsaná session cookie',
    r'(?i)Engagement Score': r'Engagement Score',
    r'(?i)Engagement Score': r'Engagement Score',
    r'(?i)normalizovaný indikátor (Engagement Score)': r'normalizovaný indikátor (Engagement Score)',
    r'(?i)Experimental projected inactive share': r'Experimental projected inactive share',
    r'(?i)Experimental projected inactive share': r'Experimental projected inactive share',
    r'(?i)Predikční výsledky jsou prezentovány pouze na agregované úrovni komunity.': r'Predikční výsledky jsou prezentovány pouze na agregované úrovni komunity.',
    r'(?i)Zaměřte se na aktivity a eventy pro komunitu.': r'Zaměřte se na aktivity a eventy pro komunitu.',
    r'(?i)Model neumožňuje automatické udělování rolí podle odhadnutého rizika.': r'Model neumožňuje automatické udělování rolí podle odhadnutého rizika.',
    r'(?i)(hypothetical usage example - riziko by teoreticky mohlo klesnout o 45 %)': r'(hypothetical usage example - riziko by teoreticky mohlo klesnout o 45 %)',
    r'(?i)(hypothetical usage example - uživatelé s vysokým skóre)': r'(hypothetical usage example - uživatelé s vysokým skóre)',
    r'(?i)(hypothetical usage example - model by mohl ukázat medián aktivity)': r'(hypothetical usage example - model by mohl ukázat medián aktivity)',
    r'(?i)Service-Oriented Architecture': r'Service-Oriented Architecture',
    r'(?i)The implementation separates routing, analytics services and data access to reduce coupling and improve testability.': r'The implementation separates routing, analytics services and data access to reduce coupling and improve testability.',
    r'(?i)The implementation separates routing, analytics services and data access.': r'The implementation separates routing, analytics services and data access.',
    r'(?i)': r'',
    r'(?i)': r'',
}

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for pattern, repl in replacements.items():
        new_content = re.sub(pattern, repl, new_content)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, _, files in os.walk('.'):
    if '.git' in root or 'node_modules' in root or '.venv' in root:
        continue
    for file in files:
        if file.endswith('.md') or file.endswith('.html') or file.endswith('.py'):
            filepath = os.path.join(root, file)
            process_file(filepath)
