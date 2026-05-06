from app.services.safe_markdown_renderer import (
    detect_unsafe_markdown_patterns,
    render_safe_markdown,
)


def test_render_safe_markdown_escapes_script_tags():
    result = render_safe_markdown("# Titulo\n<script>alert(1)</script>")

    assert "<script>" not in result.html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in result.html
    assert "script_tag" in result.blocked_patterns
    assert result.metadata["raw_html_escaped"] is True


def test_render_safe_markdown_neutralizes_event_handler_html():
    result = render_safe_markdown('<img src=x onerror=alert(1)>')

    assert "<img" not in result.html
    assert "onerror" in result.html
    assert "event_handler" in result.blocked_patterns


def test_render_safe_markdown_drops_javascript_links():
    result = render_safe_markdown("[clique](javascript:alert(1))")

    assert "href=" not in result.html
    assert "javascript:" not in result.html
    assert "clique" in result.html
    assert "javascript_url" in result.blocked_patterns


def test_render_safe_markdown_preserves_safe_http_links():
    result = render_safe_markdown("[site](https://example.com/a?b=1)")

    assert 'href="https://example.com/a?b=1"' in result.html
    assert 'rel="noopener noreferrer"' in result.html
    assert result.blocked_patterns == []


def test_render_safe_markdown_escapes_code_fence_html():
    result = render_safe_markdown("```html\n<div onclick=alert(1)>x</div>\n```")

    assert "<div" not in result.html
    assert "&lt;div onclick=alert(1)&gt;x&lt;/div&gt;" in result.html
    assert "event_handler" in result.blocked_patterns


def test_detect_unsafe_markdown_patterns_flags_iframe_and_data_url():
    patterns = detect_unsafe_markdown_patterns('<iframe src=x></iframe> [x](data:text/html,hi)')

    assert "iframe_tag" in patterns
    assert "dangerous_data_url" in patterns
