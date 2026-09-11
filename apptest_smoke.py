from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app/main.py", default_timeout=180)
at.run()

print("SCRIPT EXCEPTIONS:", at.exception)
for e in at.exception:
    print("----")
    print(e)

errors = at.error
print(f"\nst.error() calls found: {len(errors)}")
for e in errors:
    print("ERROR WIDGET:", e.value)

print("\nTabs found:", len(at.tabs))
print("Sidebar selectboxes:", [(sb.label, sb.value) for sb in at.sidebar.selectbox])
print("Plotly charts rendered:", len(at.get("plotly_chart") if hasattr(at, "get") else []))
