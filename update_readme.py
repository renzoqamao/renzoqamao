import json
import os
import re
from urllib.request import Request, urlopen

# Mapeo de colores y logos para Shields.io (puedes añadir más si aparecen otros en tus repos)
TECH_MAP = {
    "Java": {"color": "ED8B00", "logo": "openjdk"},
    "Python": {"color": "3776AB", "logo": "python"},
    "TypeScript": {"color": "3178C6", "logo": "typescript"},
    "JavaScript": {"color": "F7DF1E", "logo": "javascript"},
    "HTML": {"color": "E34F26", "logo": "html5"},
    "CSS": {"color": "1572B6", "logo": "css3"},
    "Shell": {"color": "89E051", "logo": "gnubash"},
    "C": {"color": "A8B9CC", "logo": "c"},
    "C++": {"color": "00599C", "logo": "cplusplus"},
    "Go": {"color": "00ADD8", "logo": "go"},
    "Dockerfile": {"color": "2496ED", "logo": "docker"},
    "Jupyter Notebook": {"color": "F37626", "logo": "jupyter"}
}

def make_request(url, token):
    """Realiza peticiones autenticadas a la API REST de GitHub."""
    request = Request(url)
    request.add_header("Authorization", f"token {token}")
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error en la petición a {url}: {e}")
        return None

def graphql_request(query, variables, token):
    """Realiza una consulta a la API GraphQL de GitHub."""
    payload = json.dumps({"query": query, "variables": variables}).encode()
    request = Request("https://api.github.com/graphql", data=payload)
    request.add_header("Authorization", f"bearer {token}")
    request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error en la petición GraphQL: {e}")
        return None

def make_bar(pct, width=20):
    """Devuelve una barra de progreso en texto para un porcentaje dado."""
    filled = int(round(pct / 100 * width))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)

def compute_streaks(days):
    """Calcula la racha actual y la máxima a partir de (fecha, conteo) ordenables."""
    days = sorted(days)
    longest = run = 0
    for _, count in days:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)
    current = 0
    for i, (_, count) in enumerate(reversed(days)):
        if count > 0:
            current += 1
        elif i == 0:  # hoy aún sin contribuciones: no rompe la racha
            continue
        else:
            break
    return current, longest

def fetch_contributions(login, token):
    """Devuelve (total_contribuciones, racha_actual, racha_maxima) del último año."""
    contrib_query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }
    """
    gql = graphql_request(contrib_query, {"login": login}, token)
    user_data = (gql or {}).get("data", {}).get("user")
    if not user_data:
        return 0, 0, 0
    cal = user_data["contributionsCollection"]["contributionCalendar"]
    days = [
        (d["date"], d["contributionCount"])
        for w in cal["weeks"] for d in w["contributionDays"]
    ]
    current_streak, longest_streak = compute_streaks(days)
    return cal["totalContributions"], current_streak, longest_streak

def build_stats(login, token, lang_bytes, repo_count, total_stars, total_forks, followers):
    """Genera la sección de estadísticas en texto (tabla + barras de lenguajes)."""
    total_contributions, current_streak, longest_streak = fetch_contributions(login, token)

    # Tabla resumen de métricas.
    stats_table = (
        "| 📦 Repos | ⭐ Estrellas | 🍴 Forks | 👥 Seguidores | 🔥 Contrib. (año) | 🔥 Racha | 🏆 Máx |\n"
        "|:--:|:--:|:--:|:--:|:--:|:--:|:--:|\n"
        f"| {repo_count} | {total_stars} | {total_forks} | {followers} | "
        f"{total_contributions} | {current_streak} d | {longest_streak} d |\n"
    )

    # Barras de lenguajes (top 6 por bytes de código).
    total_bytes = sum(lang_bytes.values())
    lang_lines = []
    if total_bytes:
        top_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:6]
        name_w = max(len(name) for name, _ in top_langs)
        for lang, size in top_langs:
            pct = size / total_bytes * 100
            lang_lines.append(f"{lang.ljust(name_w)}  {make_bar(pct)}  {pct:5.1f}%")
    lang_chart = "\n".join(lang_lines) if lang_lines else "Sin datos de lenguajes."

    return stats_table, lang_chart

SEPARATOR = "\n---\n"

def collect_repo_metrics(repos, token):
    """Recorre los repos (sin forks) acumulando lenguajes, estrellas y forks."""
    all_languages = set()
    lang_bytes = {}
    repo_count = total_stars = total_forks = 0
    for repo in repos:
        if repo['fork']:
            continue
        repo_count += 1
        total_stars += repo.get('stargazers_count', 0)
        total_forks += repo.get('forks_count', 0)
        langs = make_request(repo['languages_url'], token)
        if langs:
            print(f"{repo['name']}: {', '.join(langs.keys())}")
            all_languages.update(langs.keys())
            for lang, size in langs.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + size
    return all_languages, lang_bytes, repo_count, total_stars, total_forks

def build_badges(all_languages):
    """Genera las insignias (badges) Shields.io para el stack tecnológico."""
    badges = []
    for lang in sorted(all_languages):
        info = TECH_MAP.get(lang, {"color": "grey", "logo": "github"})
        clean_lang = lang.replace(" ", "%20")
        badges.append(
            f"![{lang}](https://img.shields.io/badge/-{clean_lang}-{info['color']}"
            f"?style=flat-square&logo={info['logo']}&logoColor=white)"
        )
    return " ".join(badges) if badges else "*Sin tecnologías detectadas.*"

def render_projects(repo_list, visibility_icon):
    """Construye la lista detallada en Markdown para un conjunto de repos."""
    items = []
    for r in repo_list:
        print(f"recent: {r['name']} - Actualizado el {r['updated_at']} - Privado: {r['private']}")
        items.append(f"* {visibility_icon} [{r['name']}]({r['html_url']}) - {r['description'] or 'Sin descripción'}")
    return items

def render_rest(repo_list, visibility_icon):
    """Construye una única línea con el resto de repos, separados por ' · '."""
    return " · ".join(
        f"{visibility_icon} [{r['name']}]({r['html_url']})" for r in repo_list
    )

def build_section(repo_list, visibility_icon, empty_msg):
    """Combina los 10 más recientes (detallados) con el resto en una línea."""
    top = repo_list[:10]
    rest = repo_list[10:]
    if not top:
        return empty_msg
    section = "\n".join(render_projects(top, visibility_icon))
    if rest:
        section += "\n\n" + render_rest(rest, visibility_icon)
    return section

def update_readme():
    token = os.getenv("GH_TOKEN")
    # Datos del usuario autenticado (login + seguidores)
    user_info = make_request("https://api.github.com/user", token) or {}
    login = user_info.get("login", "renzoqamao")
    followers = user_info.get("followers", 0)

    # Obtener TODOS los repositorios
    repos_url = "https://api.github.com/user/repos?per_page=100&sort=updated&visibility=all"
    repos = make_request(repos_url, token)
    print(f"Se encontraron {len(repos)} repositorios en total.")

    # Recolectar tecnologías y acumular métricas (sin repos fork)
    all_languages, lang_bytes, repo_count, total_stars, total_forks = collect_repo_metrics(repos, token)

    # Generar la sección de estadísticas en texto y las insignias del stack
    stats_table, lang_chart = build_stats(
        login, token, lang_bytes, repo_count, total_stars, total_forks, followers
    )
    tech_display = build_badges(all_languages)

    # Ordenar por fecha de actualización (más reciente primero)
    sorted_repos = sorted(repos, key=lambda x: x['updated_at'], reverse=True)

    # Filtrar el repo de perfil y separar por visibilidad
    visible_repos = [r for r in sorted_repos if r['name'] != "renzoqamao"]
    private_repos = [r for r in visible_repos if r['private']]
    public_repos = [r for r in visible_repos if not r['private']]

    private_list = build_section(private_repos, "🔒", "*Sin proyectos privados recientes.*")
    public_list = build_section(public_repos, "🌍", "*Sin proyectos públicos recientes.*")

    # Marcador que separa el encabezado escrito a mano (estático) del bloque
    # dinámico. Todo lo que esté ANTES del marcador se preserva tal cual; todo
    # lo que esté después se regenera en cada ejecución.
    MARKER = "<!-- DYNAMIC_CONTENT:START -->"

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Preservamos el encabezado estático (todo lo anterior al marcador)
    static_header = content.split(MARKER)[0].rstrip() + "\n\n"

    # Construir el nuevo bloque dinámico
    dynamic_block = [
        MARKER + "\n",
        "<!-- ⚠️ El contenido a partir de aquí se genera automáticamente con update_readme.py — no editar a mano. -->\n",
        "\n### 📊 Estadísticas de GitHub\n",
        f"\n{stats_table}",
        "\n**Lenguajes más usados**\n",
        f"\n```text\n{lang_chart}\n```\n",
        SEPARATOR,
        "\n### 🚀 Tecnologías Detectadas en mis Repositorios\n",
        f"{tech_display}\n",
        SEPARATOR,
        "\n### 📈 Últimos Proyectos\n",
        "\n**🔒 Privados**\n",
        f"{private_list}\n",
        "\n**🌍 Públicos**\n",
        f"{public_list}\n",
        SEPARATOR,
        "\n### 📫 Contacto\n",
        "[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/renzoqa)\n",
        "[![Email](https://img.shields.io/badge/Email-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:renzoquispeamao@gmail.com)\n",
        "![Ubicación](https://img.shields.io/badge/Per%C3%BA-D91023?style=for-the-badge&logoColor=white)\n"
    ]

    final_file_content = static_header + "".join(dynamic_block)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(final_file_content)
    
    print("✅ ¡README.md actualizado correctamente!")

if __name__ == "__main__":
    update_readme()