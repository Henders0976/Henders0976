#!/usr/bin/env python3
"""Gera o minigame (gh-space-shooter) com paleta azul e roxo.

Uso: make_game.py <usuario> <saida.gif> [--raw-input dados.json]
Lê GH_TOKEN do ambiente quando não há --raw-input.
"""
import sys

from gh_space_shooter.game.render_context import RenderContext
from gh_space_shooter.cli import app

_orig = RenderContext.darkmode


def _theme():
    c = _orig()
    c.background_color = (13, 17, 23)
    c.grid_color = (30, 27, 75)
    # nível 1 a 4 (menos a mais contribuições): do índigo escuro ao lavanda
    c.enemy_colors = {1: (76, 29, 149), 2: (99, 102, 241), 3: (124, 58, 237), 4: (167, 139, 250)}
    c.ship_color = (56, 189, 248)
    c.bullet_color = (196, 181, 253)
    return c


RenderContext.darkmode = staticmethod(_theme)

if __name__ == "__main__":
    user, out, *rest = sys.argv[1:]
    sys.argv = ["gh-space-shooter", user, "--output", out, *rest]
    app()
