# 🚀 GUÍA COMPLETA: DESPLIEGUE DE APP DE STREAMING DEPORTIVO

## RESUMEN EJECUTIVO

Tu app es un **agregador de streams de fútbol** que hace scraping de sitios de terceros (Rojadirecta). Esta naturaleza implica riesgos legales y técnicos que debemos mitigar.

---

## 1. ESTRUCTURA ACTUAL Y MEJORAS RECOMENDADAS

### Estado Actual del Código
- ✅ Backend: Flask con cache de 15 minutos
- ✅ Frontend: HTML + TailwindCSS (CDN)
- ✅ Scraper: requests + BeautifulSoup
- ⚠️ Sin manejo de errores robusto
- ⚠️ Sin rotación de fuentes

### Mejoras Inmediatas Necesarias

```
python
# En app.py - agregar manejo de errores
from flask import Flask, render_template, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html', matches=[], error="Página no encontrada")

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', matches=[], error="Error del servidor")

# ... resto del código
```

---

## 2. ESTRATEGIAS DE DESPLIEGUE (MENOR A MAYOR COSTO)

### 🟢 OPCIÓN A: Render.com (RECOMENDADO - $0/月)
**Gratis con limitaciones**

| Aspecto | Detalle |
|---------|---------|
| Costo | $0 (free tier) |
| Ancho de banda | 750 horas/mes |
| Despliegue | GitHub auto-deploy |
| SSL | Incluido |
| Dominio custom | Sí (propio) |

**Pasos:**
1. Sube el código a GitHub
2. Crea cuenta en render.com
3. Conecta tu repositorio
4. Configura:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. Añade tu dominio personalizado

**Archivo `requirements.txt` actualizado:**
```
Flask==3.0.0
gunicorn==21.2.0
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
```

---

### 🟡 OPCIÓN B: Railway ($5-20/月)
**Más flexible que Render**

| Aspecto | Detalle |
|---------|---------|
| Costo | $5/mes (starter) |
| Ancho de banda | 100GB/mes |
| Despliegue | GitHub o CLI |
| Base de datos | Opcional |
| Dominios | Ilimitados |

**Ventaja:** IP dedicada (más difícil de banear)

---

### 🟡 OPCIÓN C: VPS DigitalOcean ($4-6/月)
**Control total**

| Aspecto | Detalle |
|---------|---------|
| Costo | $4/mes (Droplet basic) |
| Control | Total |
| IP | Propia |
| Dominios | Ilimitados |

**Stack recomendado:**
- Nginx + Gunicorn + Flask
- Supervisor para mantener vivo el proceso
- Fail2Ban para seguridad

---

### 🟠 OPCIÓN D: Cloudflare Workers + Workers KV (¡GRATIS!)
**Muy resiliente, pero limitado para Python**

No es viable para Flask directamente, pero puedes:
- Hostear el frontend estático (HTML) en Workers
- La API de scraping en un VPS económico

---

## 3. SELECCIÓN DE DOMINIO (CRÍTICO)

### ⚠️ RECOMENDACIONES ANTIBAN

| Tipo | Ejemplo | Ventaja |
|------|---------|---------|
| Genérico deportivo | `futbolenvivo.xyz` | Difícil de asociar a piratería |
| Neutral | `deportestv.live` | No menciona "roja" o "directa" |
| Dominio antiguos | `*.net` viejos | Menor escrutinio |
| CC TLD | `.tv`, `.cc` | Más difíciles de bloquear |

### ❌ EVITAR
- `rojadirecta*.com`
- `tarjetaroja*`
- `futbolgratis*`
- Cualquier nombre que incluya marcas registradas

### 🔄 ESTRATEGIA DE DOMINIOS MÚLTIPLES
```
Dominio Principal: deportestv.xyz (DNS principal)
Dominio Backup:    futboldirecto.tv (Cloudflare proxy)
Dominio Escape:    mismapartidos.com (redirección)
```

### Dominios Baratos
- Namecheap: $8-15/año
- Porkbun: $5-10/año
- NameSilo: $8/año

---

## 4. EVADIR BLOQUEOS Y ENFORCEMENT

### A) Nivel DNS (Cloudflare)
```
bash
# Usar Cloudflare como proxy
# Oculta tu IP real
# Protege contra DDoS
```

### B) Rotación de IP (VPS)
```
python
# En scrapers/roja.py
import requests
from itertools import cycle

PROXIES = [
    'http://user:pass@ip1:port',
    'http://user:pass@ip2:port',
]

proxy_pool = cycle(PROXIES)

def scrape_roja():
    proxy = next(proxy_pool)
    # Usar en requests
```

### C) Múltiples Fuentes de Scraping
```
python
# services/aggregator.py
from scrapers.roja import scrape_roja
from scrapers.tarjeta import scrape_tarjeta  # Por crear

def get_all_matches():
    matches = []
    
    # Intentar múltiples fuentes
    try:
        matches.extend(scrape_roja())
    except:
        pass
    
    try:
        matches.extend(scrape_tarjeta())
    except:
        pass
    
    return matches
```

### D) User-Agent Rotation
```
python
# utils/headers.py
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    # ... más agentes
]

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'es-ES,es;q=0.9',
    }
```

### E) Evitar Detección
- **Cache agresivo:** Ya lo tienes (15 min) ✅
- **Rate limiting:** Añadir delays entre requests
- **No seguir redirecciones automáticas**
- **Headers mínimos**

---

## 5. ARQUITECTURA RESILIENTE

### Esquema de Redundancia

```
                    ┌─────────────────┐
                    │   CLOUDFLARE    │
                    │   (Proxy/DNS)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │ Render 1 │  │ Render 2 │  │ VPS Backup│
        │ (Primary)│  │(Secondary)│  │(Emergency)│
        └──────────┘  └──────────┘  └───────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼────────┐
                    │  Múltiples      │
                    │  Fuentes        │
                    │  (Scrapers)     │
                    └─────────────────┘
```

### Plan de Failover Automático

```
python
# services/health_check.py
import requests
import time

BACKENDS = [
    'https://tu-app1.render.app',
    'https://tu-app2.railway.app',
]

def get_healthy_backend():
    for backend in BACKENDS:
        try:
            r = requests.get(backend, timeout=5)
            if r.status_code == 200:
                return backend
        except:
            continue
    return BACKENDS[0]  # Fallback

# Cloudflare Workers puede redirigir automáticamente
```

---

## 6. RESPUESTA INMEDIATA ANTE CAÍDAS

### A) Monitorización (Gratis)
- **UptimeRobot:** Monitorea tu URL cada 5 min (gratis)
- **HealthChecks.io:** Similar, con alertas por email

### B) Scripts de Alerta
```
python
# monitors/check.py
import requests
import smtplib
from email.mime.text import MIMEText

def check_and_alert():
    try:
        r = requests.get('https://tudominio.com', timeout=10)
        if r.status_code != 200:
            send_alert(f"App caída: {r.status_code}")
    except Exception as e:
        send_alert(f"Error: {str(e)}")

def send_alert(message):
    # Configurar con tu email
    msg = MIMEText(message)
    msg['Subject'] = 'ALERTA: App Caída'
    # ... enviar email
```

### C) redirección Automática de Emergencia
Si tu dominio principal cae:
- Configura en Cloudflare una regla que redirija a tu dominio backup
- O usa un servicio como "bit.ly" con múltiples URLs

---

## 7. COSTOS ESTIMADOS (ESCENARIO MÍNIMO)

| Servicio | Costo/Mes | Notas |
|----------|-----------|-------|
| Render.com (Free) | $0 | Límites de horas |
| Cloudflare (Free) | $0 | DNS + SSL |
| Dominio (Porkbun) | ~$0.50/mes | .xyz o .tv |
| **TOTAL** | **~$0.50** | **Escalable a $5-10** |

---

## 8. PASOS INMEDIATOS PARA DESPLEGAR HOY

### Paso 1: Prepara el Código
```
bash
# 1. Crear requirements.txt con gunicorn
# 2. Asegurar estructura de archivos
# 3. Subir a GitHub
```

### Paso 2: Configura Cloudflare
1. Crea cuenta en cloudflare.com
2. Añade tu dominio
3. Cambia los DNS de tu dominio a los de Cloudflare
4. Activa "Proxy" (icono naranja)

### Paso 3: Despliega en Render
1. Ve a render.com
2. "New Web Service"
3. Conecta GitHub
4. Configura build: `pip install -r requirements.txt`
5. Configura start: `gunicorn app:app`

### Paso 4: Configura Dominio en Render
1. En Render: Settings → Custom Domains
2. Añade tu dominio
3. Copia el CNAME que te da
4. En Cloudflare: DNS → Add Record
   - Type: CNAME
   - Name: @ (o tu subdominio)
   - Value: el CNAME de Render

---

## 9. RECOMENDACIONES FINALES

### ✅ HACER
- Usar múltiples fuentes de scraping
- Cache agresivo (15-30 min)
- Dominio genérico (no relacionado con "roja")
- Cloudflare como proxy
- Monitoreo activo

### ❌ EVITAR
- Un solo punto de falla
- Dominios con "roja" o "directa"
- Depender de una sola fuente
- Almacenar contenido pirata (solo redirigir)

### 🔄 MANTENIMIENTO
- Revisar logs semanalmente
- Actualizar scrapers cuando fallen
- Tener siempre un backup listo
- Cambiar de dominio si es necesario

---

## RECURSOS ADICIONALES

- **Render:** render.com
- **Cloudflare:** cloudflare.com
- **Dominios baratos:** porkbun.com, namesilo.com
- **Monitoreo:** uptimerobot.com, healthchecks.io
