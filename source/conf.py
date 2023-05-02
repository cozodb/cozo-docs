# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

release = '0.7'
project = 'The Cozo Database Manual ' + release
author = 'Ziyang Hu'
copyright = '2023, ' + author

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'nbsphinx',
    'myst_parser',
    'sphinx_toolbox.sidebar_links',
    'sphinx_toolbox.github',
    'sphinx_copybutton'
]

myst_enable_extensions = [
    "amsmath",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    # "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

github_username = 'cozodb'
github_repository = 'cozo'

templates_path = ['_templates']
exclude_patterns = []

add_function_parentheses = False
add_module_names = False
latex_show_urls = 'footnote'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
html_css_files = ['override.css']
html_title = "CozoDB v" + release
# html_baseurl = '/'
