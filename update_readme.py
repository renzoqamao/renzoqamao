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

    # Obtener los 10 proyectos más recientes (por fecha de actualizacion)
    recent = sorted(repos, key=lambda x: x['updated_at'], reverse=True)[:10]
    
    project_items = []
    for r in recent:
        print(f"recent: {r['name']} - Actualizado el {r['updated_at']} - Privado: {r['private']}")
        if( "renzoqamao"==r['name']):
            continue;
        visibility = "🔒" if r['private'] else "🌍"
        project_items.append(f"* {visibility} [{r['name']}]({r['html_url']}) - {r['description'] or 'Sin descripción'}")
    
    project_list = "\n".join(project_items)

    with open("README.md", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Preservamos el encabezado original (líneas 1 a 17)
    original_header = lines[:17]

    # Construir el nuevo bloque dinámico
    new_content = [
        "\n### 🚀 Tecnologías Detectadas en mis Repositorios\n",
        f"{tech_display}\n",
        "\n---\n",
        "\n### 📈 Últimos Proyectos\n",
        f"{project_list}\n",
        "\n---\n",
        "\n### 📫 Contacto\n",
        "* **LinkedIn:** [linkedin.com/in/renzoqa](https://www.linkedin.com/in/renzoqa)\n",
        "* **Email:** [renzoquispeamao@gmail.com](mailto:renzoquispeamao@gmail.com)\n",
        "* **Ubicación:** Perú 🇵🇪\n"
    ]

    final_file_content = "".join(original_header) + "".join(new_content)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(final_file_content)
    
    print("✅ ¡README.md actualizado correctamente!")

if __name__ == "__main__":
    update_readme()