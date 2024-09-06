from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode

from docutils import nodes
from docutils.parsers.rst.directives import path
from sphinx.addnodes import download_reference
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata
from sphinx.writers.html5 import HTML5Translator
from sphinx.writers.latex import LaTeXTranslator

KPM_PATH = "_static/kpm/index.html"


class KPMNode(nodes.container):
    def __init__(
        self,
        depth: int,
        preview: bool,
        spec_ref: Optional[str],
        graph_ref: Optional[str],
        height: Optional[str],
    ) -> None:
        # we're leveraging the builtin download_reference node
        # to automatically move necessary files from sources
        # into the build directory and have a path to them
        spec_node = graph_node = None
        if spec_ref:
            spec_node = download_reference("", "", reftarget=spec_ref, disabled=True)
        if graph_ref:
            graph_node = download_reference("", "", reftarget=graph_ref, disabled=True)

        super().__init__("", *(node for node in (spec_node, graph_node) if node))
        self.spec_node = spec_node
        self.graph_node = graph_node
        self.rel_pfx = "../" * depth
        self.preview = preview
        self.height = height

    def _node_to_target(self, node: download_reference) -> str:
        if "filename" in node:
            return "relative://../../_downloads/" + node["filename"]
        elif "refuri" in node:
            return node["refuri"]

        raise ValueError("The KPM file path is neither a valid file nor a URL")

    @staticmethod
    def visit_html(trans: HTML5Translator, node: KPMNode):
        params = {}
        if node.spec_node:
            params["spec"] = node._node_to_target(node.spec_node)
        if node.graph_node:
            params["graph"] = node._node_to_target(node.graph_node)
        if node.preview:
            params["preview"] = str(node.preview).lower()

        trans.body.append(
            f"""
<iframe src='{node.rel_pfx}{KPM_PATH}?{urlencode(params)}'
    allow='fullscreen'
        style='
            width:100%;
            {"height:" + node.height if node.height else "aspect-ratio:3/2"};
            border:none;
        '
></iframe>"""
        )

    @staticmethod
    def visit_latex(trans: LaTeXTranslator, _: KPMNode):
        trans.body.append(
            r"""
\begin{sphinxadmonition}{warning}{Note:}
\sphinxAtStartPar
An interactive KPM frame, where you can explore the block design for this section,
is available here in the HTML version of this documentation.
\end{sphinxadmonition}"""
        )

    @staticmethod
    def depart_node(*_):
        pass


class KPMDirective(SphinxDirective):
    option_spec = {"spec": path, "dataflow": path, "preview": bool, "height": str}

    def run(self) -> list[nodes.Node]:
        return [
            KPMNode(
                self.env.docname.count("/"),
                self.options.get("preview", False),
                self.options.get("spec"),
                self.options.get("dataflow"),
                self.options.get("height"),
            )
        ]


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_node(
        KPMNode,
        html=(KPMNode.visit_html, KPMNode.depart_node),
        latex=(KPMNode.visit_latex, KPMNode.depart_node),
    )
    app.add_directive("kpm_iframe", KPMDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
