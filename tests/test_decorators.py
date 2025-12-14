"""Tests for extract_kwargs decorator."""

from genro_toolbox import extract_kwargs


class DummyClass:
    """Dummy class for testing extract_kwargs decorator (requires self)."""

    pass


class TestExtractKwargsBasic:
    """Basic extract_kwargs functionality."""

    def test_extract_with_prefix(self):
        """Test extracting kwargs with prefix."""
        dummy = DummyClass()

        @extract_kwargs(logging=True)
        def func(self, name, logging_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "other": kwargs}

        result = func(
            dummy, name="test", logging_level="INFO", logging_format="json", timeout=30
        )

        assert result["logging"] == {"level": "INFO", "format": "json"}
        assert result["other"] == {"timeout": 30}

    def test_extract_multiple_prefixes(self):
        """Test extracting multiple prefix groups."""
        dummy = DummyClass()

        @extract_kwargs(logging=True, cache=True)
        def func(self, name, logging_kwargs=None, cache_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "cache": cache_kwargs, "other": kwargs}

        result = func(
            dummy,
            name="test",
            logging_level="INFO",
            cache_ttl=300,
            cache_backend="redis",
            timeout=30,
        )

        assert result["logging"] == {"level": "INFO"}
        assert result["cache"] == {"ttl": 300, "backend": "redis"}
        assert result["other"] == {"timeout": 30}

    def test_no_extracted_kwargs(self):
        """Test when no kwargs match prefix - returns empty dict (not None)."""
        dummy = DummyClass()

        @extract_kwargs(logging=True)
        def func(self, name, logging_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "other": kwargs}

        result = func(dummy, name="test", timeout=30)

        # Original behavior: always returns dict(), never None
        assert result["logging"] == {}
        assert result["other"] == {"timeout": 30}

    def test_extract_with_pop_false(self):
        """Test extraction with pop=False (keeps params in source)."""
        dummy = DummyClass()

        @extract_kwargs(logging={"pop": False})
        def func(self, name, logging_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "other": kwargs}

        result = func(dummy, name="test", logging_level="INFO", timeout=30)

        # With pop=False, params stay in kwargs
        assert result["logging"] == {"level": "INFO"}
        assert result["other"] == {"timeout": 30, "logging_level": "INFO"}

    def test_extract_with_slice_prefix_false(self):
        """Test extraction without slicing prefix."""
        dummy = DummyClass()

        @extract_kwargs(logging={"slice_prefix": False, "pop": True})
        def func(self, name, logging_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "other": kwargs}

        result = func(dummy, name="test", logging_level="INFO", timeout=30)

        # With slice_prefix=False, keys keep the prefix
        assert result["logging"] == {"logging_level": "INFO"}
        assert result["other"] == {"timeout": 30}

    def test_reserved_class_keyword(self):
        """Test that 'class' keyword is renamed to '_class'."""
        dummy = DummyClass()

        @extract_kwargs(logging=True)
        def func(self, name, logging_kwargs=None, **kwargs):
            return {"logging": logging_kwargs}

        result = func(dummy, name="test", logging_class="MyLogger")

        # Reserved word 'class' becomes '_class'
        assert result["logging"] == {"_class": "MyLogger"}

    def test_merge_with_existing_kwargs(self):
        """Test merging extracted kwargs with explicitly passed kwargs dict."""
        dummy = DummyClass()

        @extract_kwargs(logging=True)
        def func(self, name, logging_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "other": kwargs}

        # Pass both logging_kwargs explicitly AND prefixed params
        result = func(
            dummy,
            name="test",
            logging_kwargs={"existing": "value"},
            logging_level="INFO",
            timeout=30,
        )

        # Should merge
        assert result["logging"] == {"existing": "value", "level": "INFO"}
        assert result["other"] == {"timeout": 30}

    def test_dictkwargs_parameter(self):
        """Test _dictkwargs parameter to pass dict directly."""
        dummy = DummyClass()

        extract_spec = {"logging": True, "cache": True}

        @extract_kwargs(_dictkwargs=extract_spec)
        def func(self, name, logging_kwargs=None, cache_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "cache": cache_kwargs}

        result = func(dummy, name="test", logging_level="INFO", cache_ttl=300)

        assert result["logging"] == {"level": "INFO"}
        assert result["cache"] == {"ttl": 300}

    def test_non_dict_kwargs_parameter(self):
        """Test that non-dict values for {prefix}_kwargs are handled gracefully."""

        @extract_kwargs(logging=True)
        def func(logging_kwargs=None, **kwargs):
            return logging_kwargs

        # Pass a non-dict value for logging_kwargs (edge case)
        result = func(logging_kwargs=123, logging_level="INFO")

        # Should convert to dict and merge with extracted kwargs
        assert result == {"level": "INFO"}

    def test_extract_with_non_true_non_dict_value(self):
        """Test extraction with values other than True or dict."""

        @extract_kwargs(logging=False)  # Use False instead of True or dict
        def func(logging_kwargs=None, **kwargs):
            return {"logging": logging_kwargs, "remaining": kwargs}

        result = func(logging_level="INFO", other="value")

        # Should use default options (don't pop)
        assert result["logging"] == {"level": "INFO"}
        assert result["remaining"] == {"logging_level": "INFO", "other": "value"}


class TestExtractKwargsAdapter:
    """Test _adapter functionality."""

    def test_adapter_called(self):
        """Test that _adapter method is called if present."""

        class ClassWithAdapter:
            def __init__(self):
                self.adapter_called = False
                self.adapter_kwargs = None

            def my_adapter(self, kwargs):
                self.adapter_called = True
                self.adapter_kwargs = dict(kwargs)
                # Adapter can modify kwargs
                kwargs["modified_by_adapter"] = True

            @extract_kwargs(_adapter="my_adapter", logging=True)
            def my_method(self, name, logging_kwargs=None, **kwargs):
                return {"logging": logging_kwargs, "other": kwargs}

        obj = ClassWithAdapter()
        result = obj.my_method(name="test", logging_level="INFO", timeout=30)

        # Adapter should have been called
        assert obj.adapter_called is True
        assert obj.adapter_kwargs is not None
        # Adapter's modification should be visible
        assert result["other"]["modified_by_adapter"] is True

    def test_adapter_not_present(self):
        """Test that missing _adapter doesn't cause error."""

        class ClassWithoutAdapter:
            @extract_kwargs(_adapter="nonexistent_adapter", logging=True)
            def my_method(self, name, logging_kwargs=None, **kwargs):
                return {"logging": logging_kwargs, "other": kwargs}

        obj = ClassWithoutAdapter()
        # Should not raise error even if adapter doesn't exist
        result = obj.my_method(name="test", logging_level="INFO")

        assert result["logging"] == {"level": "INFO"}
