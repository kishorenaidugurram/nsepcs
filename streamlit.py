"""
Mock streamlit module for standalone script execution
This allows streamlit_app.py to be imported without actually running Streamlit
"""

class MockStreamlit:
    """Mock object for streamlit module"""

    def __getattr__(self, name):
        """Return mock functions for any streamlit call"""
        return lambda *args, **kwargs: None

    def set_page_config(self, *args, **kwargs):
        pass

    def markdown(self, *args, **kwargs):
        pass

    def columns(self, *args, **kwargs):
        class MockCol:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return [MockCol()] * args[0] if args else []

    def container(self):
        class MockContainer:
            def metric(self, *args, **kwargs):
                pass
            def markdown(self, *args, **kwargs):
                pass
        return MockContainer()

    def empty(self):
        return self

    def progress(self, *args, **kwargs):
        return self

    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass

    def success(self, *args, **kwargs):
        pass

    def session_state(self):
        return {}

    def button(self, *args, **kwargs):
        return False

    def selectbox(self, *args, **kwargs):
        return kwargs.get('options', [None])[0]

    def dataframe(self, *args, **kwargs):
        pass

    def write(self, *args, **kwargs):
        pass

    def tabs(self, *args, **kwargs):
        class MockTab:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return [MockTab()] * len(args[0]) if args and isinstance(args[0], (list, tuple)) else []

    def plotly_chart(self, *args, **kwargs):
        pass

    def metric(self, *args, **kwargs):
        pass

    def checkbox(self, *args, **kwargs):
        return False

    def slider(self, *args, **kwargs):
        return kwargs.get('value', 0) if 'value' in kwargs else 0

    def multiselect(self, *args, **kwargs):
        return kwargs.get('default', [])

    def number_input(self, *args, **kwargs):
        return kwargs.get('value', 0) if 'value' in kwargs else 0

    def text_input(self, *args, **kwargs):
        return kwargs.get('value', '') if 'value' in kwargs else ''

    def download_button(self, *args, **kwargs):
        return False

    def selectbox(self, *args, **kwargs):
        return kwargs.get('options', [None])[0]

    @property
    def session_state(self):
        return {}

# Create a singleton instance
_st = MockStreamlit()

# Decorators
def cache_data(ttl=None, show_spinner=True):
    """Mock cache_data decorator"""
    def decorator(func):
        return func
    return decorator

def cache_resource():
    """Mock cache_resource decorator"""
    def decorator(func):
        return func
    return decorator

# Expose as module-level attributes
set_page_config = _st.set_page_config
markdown = _st.markdown
columns = _st.columns
container = _st.container
empty = _st.empty
progress = _st.progress
info = _st.info
warning = _st.warning
error = _st.error
success = _st.success
session_state = _st.session_state
button = _st.button
selectbox = _st.selectbox
dataframe = _st.dataframe
write = _st.write
tabs = _st.tabs
plotly_chart = _st.plotly_chart
metric = _st.metric
checkbox = _st.checkbox
slider = _st.slider
multiselect = _st.multiselect
number_input = _st.number_input
text_input = _st.text_input
download_button = _st.download_button
