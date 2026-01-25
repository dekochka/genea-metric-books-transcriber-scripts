"""
Unit tests for PromptAssemblyEngine
"""
import os
import pytest
import tempfile
import shutil
from wizard.prompt_assembler import PromptAssemblyEngine


@pytest.fixture
def temp_templates_dir():
    """Create a temporary directory with test templates."""
    temp_dir = tempfile.mkdtemp()
    templates_dir = os.path.join(temp_dir, "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # Create a test template
    template_content = """# Test Template

## Context

{{ARCHIVE_REFERENCE}}
{{DOCUMENT_DESCRIPTION}}
{{DATE_RANGE}}

## Villages:
Main related to document:
{{MAIN_VILLAGES}}

May appear in document:
{{ADDITIONAL_VILLAGES}}

## Common Surnames:
{{COMMON_SURNAMES}}

## Fond Number:
{{FOND_NUMBER}}

## Main Village:
{{MAIN_VILLAGE_NAME}} ({{MAIN_VILLAGE_NAME_LATIN}})
"""
    
    template_path = os.path.join(templates_dir, "test-template.md")
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    yield templates_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def assembler(temp_templates_dir):
    """Create PromptAssemblyEngine with test templates."""
    return PromptAssemblyEngine(templates_dir=temp_templates_dir)


class TestPromptAssemblyEngine:
    """Test cases for PromptAssemblyEngine."""
    
    def test_init_default_templates_dir(self):
        """Test initialization with default templates directory."""
        engine = PromptAssemblyEngine()
        assert engine.templates_dir is not None
        assert os.path.isdir(engine.templates_dir) or os.path.isdir(os.path.dirname(engine.templates_dir))
    
    def test_init_custom_templates_dir(self, temp_templates_dir):
        """Test initialization with custom templates directory."""
        engine = PromptAssemblyEngine(templates_dir=temp_templates_dir)
        assert engine.templates_dir == temp_templates_dir
    
    def test_load_template_success(self, assembler):
        """Test loading an existing template."""
        template = assembler._load_template("test-template")
        assert template is not None
        assert "Test Template" in template
        assert "{{ARCHIVE_REFERENCE}}" in template
    
    def test_load_template_not_found(self, assembler):
        """Test loading a non-existent template raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            assembler._load_template("non-existent-template")
    
    def test_replace_variables_basic(self, assembler):
        """Test basic variable replacement."""
        template = "Archive: {{ARCHIVE_REFERENCE}}"
        context = {
            'archive_reference': 'Ф. 487, оп. 1, спр. 545'
        }
        result = assembler._replace_variables(template, context)
        assert "{{ARCHIVE_REFERENCE}}" not in result
        assert "Ф. 487, оп. 1, спр. 545" in result
    
    def test_replace_variables_all_fields(self, assembler):
        """Test replacement of all template variables."""
        template = """{{ARCHIVE_REFERENCE}}
{{DOCUMENT_DESCRIPTION}}
{{DATE_RANGE}}
{{MAIN_VILLAGES}}
{{ADDITIONAL_VILLAGES}}
{{COMMON_SURNAMES}}
{{FOND_NUMBER}}
{{MAIN_VILLAGE_NAME}}
{{MAIN_VILLAGE_NAME_LATIN}}"""
        
        context = {
            'archive_reference': 'Ф. 487, оп. 1, спр. 545',
            'document_type': 'Birth records',
            'date_range': '1850-1900',
            'main_villages': [
                {'name': 'Княжа', 'variants': ['Knyazha', 'Kniazha']}
            ],
            'additional_villages': [
                {'name': 'Шубино', 'variants': []}
            ],
            'common_surnames': ['Іванов', 'Петров', 'Сидоров']
        }
        
        result = assembler._replace_variables(template, context)
        
        assert "{{ARCHIVE_REFERENCE}}" not in result
        assert "{{DOCUMENT_DESCRIPTION}}" not in result
        assert "Ф. 487, оп. 1, спр. 545" in result
        assert "Birth records" in result
        assert "1850-1900" in result
        assert "Княжа" in result
        assert "Knyazha" in result
        assert "Шубино" in result
        assert "Іванов" in result
        assert "487" in result  # Fond number extracted
    
    def test_format_villages_with_variants(self, assembler):
        """Test village formatting with variants."""
        villages = [
            {'name': 'Княжа', 'variants': ['Knyazha', 'Kniazha']},
            {'name': 'Шубино', 'variants': []}
        ]
        result = assembler._format_villages(villages, is_main=True)
        assert "Княжа" in result
        assert "Knyazha" in result
        assert "Шубино" in result
    
    def test_format_villages_empty(self, assembler):
        """Test formatting empty village list."""
        result = assembler._format_villages([], is_main=True)
        assert result == ""
    
    def test_format_villages_string_fallback(self, assembler):
        """Test village formatting with string fallback."""
        villages = ["Княжа", "Шубино"]
        result = assembler._format_villages(villages, is_main=True)
        assert "Княжа" in result
        assert "Шубино" in result
    
    def test_format_surnames(self, assembler):
        """Test surname formatting."""
        surnames = ['Іванов', 'Петров', 'Сидоров']
        result = assembler._format_surnames(surnames)
        assert "Іванов" in result
        assert "Петров" in result
        assert "Сидоров" in result
        assert ", " in result  # Should be comma-separated
    
    def test_format_surnames_empty(self, assembler):
        """Test formatting empty surname list."""
        result = assembler._format_surnames([])
        assert result == ""
    
    def test_extract_fond_number(self, assembler):
        """Test fond number extraction from archive reference."""
        template = "{{FOND_NUMBER}}"
        context = {
            'archive_reference': 'Ф. 487, оп. 1, спр. 545'
        }
        result = assembler._replace_variables(template, context)
        assert "487" in result
    
    def test_extract_fond_number_missing(self, assembler):
        """Test fond number extraction when not present."""
        template = "{{FOND_NUMBER}}"
        context = {
            'archive_reference': 'No fond number here'
        }
        result = assembler._replace_variables(template, context)
        assert result == ""  # Should be empty string
    
    def test_main_village_name_extraction(self, assembler):
        """Test main village name extraction."""
        template = "{{MAIN_VILLAGE_NAME}} ({{MAIN_VILLAGE_NAME_LATIN}})"
        context = {
            'main_villages': [
                {'name': 'Княжа', 'variants': ['Knyazha']}
            ]
        }
        result = assembler._replace_variables(template, context)
        assert "Княжа" in result
        assert "Knyazha" in result
    
    def test_assemble_complete_flow(self, assembler):
        """Test complete assembly flow."""
        context = {
            'archive_reference': 'Ф. 487, оп. 1, спр. 545',
            'document_type': 'Birth records',
            'date_range': '1850-1900',
            'main_villages': [
                {'name': 'Княжа', 'variants': ['Knyazha']}
            ],
            'additional_villages': [],
            'common_surnames': ['Іванов', 'Петров']
        }
        
        result = assembler.assemble("test-template", context)
        
        assert "{{ARCHIVE_REFERENCE}}" not in result
        assert "Ф. 487, оп. 1, спр. 545" in result
        assert "Birth records" in result
        assert "Княжа" in result
    
    def test_list_templates(self, assembler):
        """Test listing available templates."""
        templates = assembler.list_templates()
        assert len(templates) > 0
        assert any(t['name'] == 'test-template' for t in templates)
    
    def test_get_template_info_exists(self, assembler):
        """Test getting info for existing template."""
        info = assembler.get_template_info("test-template")
        assert info['exists'] is True
        assert info['name'] == 'test-template'
        assert 'path' in info
    
    def test_get_template_info_not_exists(self, assembler):
        """Test getting info for non-existent template."""
        info = assembler.get_template_info("non-existent")
        assert info['exists'] is False
    
    def test_unreplaced_variables_warning(self, assembler, caplog):
        """Test that unreplaced variables trigger a warning."""
        template = "{{UNKNOWN_VARIABLE}}"
        context = {}
        result = assembler._replace_variables(template, context)
        # Variable should remain unreplaced
        assert "{{UNKNOWN_VARIABLE}}" in result
        # Warning should be logged
        assert "Unreplaced template variables" in caplog.text
