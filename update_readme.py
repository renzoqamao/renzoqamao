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
    """Realiza peticiones autenticadas a la API de GitHub."""
    request = Request(url)
    request.add_header("Authorization", f"token {token}")
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error en la petición a {url}: {e}")
        return None

def update_readme():
    token = os.getenv("GH_TOKEN")
    # Obtener TODOS los repositorios
    repos_url = "https://api.github.com/user/repos?per_page=100&sort=updated&visibility=all"
    repos = make_request(repos_url, token)
    print(f"Se encontraron {len(repos)} repositorios en total.")

    # Recolectar tecnologías
    all_languages = set()
    for repo in repos:
        if not repo['fork']:
            langs = make_request(repo['languages_url'], token)
            if langs:
                new_langs = list(langs.keys())
                print(f"{repo['name']}: {', '.join(new_langs)}")
                all_languages.update(new_langs)

    # Crear insignias (badges) para el stack tecnológico
    badges = []
    for lang in sorted(list(all_languages)):
        info = TECH_MAP.get(lang, {"color": "grey", "logo": "github"})
        logo = info['logo']
        color = info['color']
        # Limpiar espacios para la URL del badge
        clean_lang = lang.replace(" ", "%20")
        badge = f"![{lang}](https://img.shields.io/badge/-{clean_lang}-{color}?style=flat-square&logo={logo}&logoColor=white)"
        badges.append(badge)
    
    tech_display = " ".join(badges) if badges else "*Sin tecnologías detectadas.*"

    # Ordenar por fecha de actualización (más reciente primero)
    sorted_repos = sorted(repos, key=lambda x: x['updated_at'], reverse=True)

    def render_projects(repo_list, visibility_icon):
        """Construye la lista en Markdown para un conjunto de repos."""
        items = []
        for r in repo_list:
            print(f"recent: {r['name']} - Actualizado el {r['updated_at']} - Privado: {r['private']}")
            items.append(f"* {visibility_icon} [{r['name']}]({r['html_url']}) - {r['description'] or 'Sin descripción'}")
        return items

    # Filtrar el repo de perfil y separar por visibilidad (últimos 10 de cada uno)
    visible_repos = [r for r in sorted_repos if r['name'] != "renzoqamao"]
    private_repos = [r for r in visible_repos if r['private']][:10]
    public_repos = [r for r in visible_repos if not r['private']][:10]

    private_list = "\n".join(render_projects(private_repos, "🔒")) or "*Sin proyectos privados recientes.*"
    public_list = "\n".join(render_projects(public_repos, "🌍")) or "*Sin proyectos públicos recientes.*"

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
        "\n### 🚀 Tecnologías Detectadas en mis Repositorios\n",
        f"{tech_display}\n",
        "\n---\n",
        "\n### 📈 Últimos Proyectos\n",
        "\n**🔒 Privados**\n",
        f"{private_list}\n",
        "\n**🌍 Públicos**\n",
        f"{public_list}\n",
        "\n---\n",
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