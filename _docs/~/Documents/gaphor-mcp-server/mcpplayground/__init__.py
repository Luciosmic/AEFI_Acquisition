import logging
from mcp.server.fastmcp import FastMCP, Context
from gaphor.storage import storage
from gaphor.core.modeling import ElementFactory, Diagram
from gaphor.services.modelinglanguage import ModelingLanguageService
from gaphor import UML

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


mcp = FastMCP("Gaphor")

element_factory = ElementFactory()
modeling_language = ModelingLanguageService()
current_model_file = None


@mcp.tool()
def load_gaphor_model(filename: str) -> str:
    """Load a Gaphor model from the file system"""
    global current_model_file
    logger.info(f"Loading model from file {filename}")
    try:
        with open(filename, "rb") as fd:
            storage.load(fd, element_factory=element_factory, modeling_language=modeling_language)
        current_model_file = filename
        return f"Loaded model {filename}"
    except Exception as e:
        logger.error(f"Could not load model from file {filename}: {e}")
        return f"Could not load model from file {filename}: {e}"


@mcp.tool()
def find_model_elements_by_name(name: str) -> list[str]:
    """Find model elements by name model elements of a specific type.
    
    Types can be "Class", "Interface", "Actor".
    """
    logger.info("Looking for elements by name %s", name)

    if not name:
        return ["No name provided."]
    n = name.lower()

    found = [
        f"{type(element).__name__}: {element.name}" for element in element_factory.select(
            lambda e: hasattr(e, "name") and n in (e.name or "").lower()
        )
    ]
    logger.info(f"Found: {found}")
    return found


@mcp.tool()
def query_model_elements_of_type(element_type: str) -> list[str]:
    """Query model elements of a specific type.
    
    Types can be "Class", "Interface", "Actor", "Package", etc.
    """
    model_type = modeling_language.lookup_element(element_type)
    logger.info(f"Looking for elements of type {model_type} (from {element_type})")
    if not model_type:
        return [f"Invalid element type {element_type}. Valid types are: Class, Interface, Actor, Package."]

    found = [
        f"{type(element).__name__}: {element.name}" for element in element_factory.select(model_type)
    ]
    logger.info(f"Found: {found}")
    return found


@mcp.tool()
def create_element(element_type: str, name: str, package_name: str = None) -> str:
    """Create a new element in the model.
    
    Args:
        element_type: Type of element to create (Class, Interface, Package, etc.)
        name: Name for the new element
        package_name: Optional name of package to add element to
    """
    model_type = modeling_language.lookup_element(element_type)
    if not model_type:
        return f"Invalid element type {element_type}"
    
    try:
        element = element_factory.create(model_type)
        element.name = name
        
        # If package specified, try to find it and add element to it
        if package_name:
            packages = element_factory.select(
                lambda e: hasattr(e, "name") and e.name == package_name
            )
            for pkg in packages:
                if hasattr(pkg, "packagedElement"):
                    pkg.packagedElement = element
                    break
        
        logger.info(f"Created {element_type} '{name}'")
        return f"Created {element_type} '{name}' (id: {element.id})"
    except Exception as e:
        logger.error(f"Error creating element: {e}")
        return f"Error creating element: {e}"


@mcp.tool()
def modify_element_name(element_name: str, new_name: str) -> str:
    """Modify the name of an existing element.
    
    Args:
        element_name: Current name of the element
        new_name: New name for the element
    """
    try:
        elements = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == element_name
        )
        if not elements:
            return f"Element '{element_name}' not found"
        
        element = next(iter(elements))
        old_name = element.name
        element.name = new_name
        logger.info(f"Renamed '{old_name}' to '{new_name}'")
        return f"Renamed '{old_name}' to '{new_name}'"
    except Exception as e:
        logger.error(f"Error modifying element: {e}")
        return f"Error modifying element: {e}"


@mcp.tool()
def save_gaphor_model(filename: str = None) -> str:
    """Save the current model to a file.
    
    Args:
        filename: File path to save to. If not provided, saves to the loaded file.
    """
    global current_model_file
    save_file = filename or current_model_file
    
    if not save_file:
        return "No file specified and no model loaded. Use load_gaphor_model first or provide a filename."
    
    try:
        with open(save_file, "wb") as fd:
            storage.save(fd, element_factory=element_factory)
        logger.info(f"Saved model to {save_file}")
        return f"Saved model to {save_file}"
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        return f"Error saving model: {e}"


# ============================================================================
# DIAGRAM CREATION TOOLS (NOT FULLY VALIDATED - based on documentation)
# ============================================================================

@mcp.tool()
def create_diagram(name: str, package_name: str = None) -> str:
    """Create a new diagram in the model.
    
    NOTE: This function is NOT FULLY VALIDATED. Based on documentation examples.
    
    Args:
        name: Name for the diagram
        package_name: Optional name of package to add diagram to
    """
    try:
        diagram = element_factory.create(Diagram)
        diagram.name = name
        
        # If package specified, try to find it and add diagram to it
        if package_name:
            packages = element_factory.select(
                lambda e: hasattr(e, "name") and e.name == package_name
            )
            for pkg in packages:
                if hasattr(pkg, "ownedDiagram"):
                    pkg.ownedDiagram = diagram
                    break
        
        logger.info(f"Created diagram '{name}'")
        return f"Created diagram '{name}' (id: {diagram.id})"
    except Exception as e:
        logger.error(f"Error creating diagram: {e}")
        return f"Error creating diagram: {e}"


@mcp.tool()
def add_element_to_diagram(element_name: str, diagram_name: str, x: float = 0.0, y: float = 0.0) -> str:
    """Add an element to a diagram (drop function).
    
    NOTE: This function is NOT FULLY VALIDATED. Based on documentation examples.
    
    Args:
        element_name: Name of the element to add
        diagram_name: Name of the diagram
        x: X position on diagram (default: 0.0)
        y: Y position on diagram (default: 0.0)
    """
    try:
        from gaphor.diagram.drop import drop
        
        # Find element
        elements = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == element_name
        )
        if not elements:
            return f"Element '{element_name}' not found"
        element = next(iter(elements))
        
        # Find diagram
        diagrams = element_factory.select(
            lambda e: isinstance(e, Diagram) and hasattr(e, "name") and e.name == diagram_name
        )
        if not diagrams:
            return f"Diagram '{diagram_name}' not found"
        diagram = next(iter(diagrams))
        
        # Drop element on diagram
        result = drop(element, diagram, x, y)
        logger.info(f"Added element '{element_name}' to diagram '{diagram_name}'")
        return f"Added element '{element_name}' to diagram '{diagram_name}'"
    except Exception as e:
        logger.error(f"Error adding element to diagram: {e}")
        return f"Error adding element to diagram: {e}"


@mcp.tool()
def create_dependency(client_name: str, supplier_name: str, label: str = "") -> str:
    """Create a dependency relationship between two elements.
    
    NOTE: This function is NOT FULLY VALIDATED. Based on documentation examples.
    
    Args:
        client_name: Name of the client element (depends on)
        supplier_name: Name of the supplier element (depended upon)
        label: Optional label for the dependency
    """
    try:
        # Find client
        clients = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == client_name
        )
        if not clients:
            return f"Client element '{client_name}' not found"
        client = next(iter(clients))
        
        # Find supplier
        suppliers = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == supplier_name
        )
        if not suppliers:
            return f"Supplier element '{supplier_name}' not found"
        supplier = next(iter(suppliers))
        
        # Create dependency
        dependency = element_factory.create(UML.Dependency)
        dependency.client = client
        dependency.supplier = supplier
        if label:
            dependency.name = label
        
        logger.info(f"Created dependency from '{client_name}' to '{supplier_name}'")
        return f"Created dependency from '{client_name}' to '{supplier_name}'"
    except Exception as e:
        logger.error(f"Error creating dependency: {e}")
        return f"Error creating dependency: {e}"


@mcp.tool()
def create_realization(implementing_name: str, interface_name: str) -> str:
    """Create a realization relationship (interface implementation).
    
    NOTE: This function is NOT FULLY VALIDATED. Based on documentation examples.
    
    Args:
        implementing_name: Name of the class implementing the interface
        interface_name: Name of the interface being implemented
    """
    try:
        # Find implementing class
        implementers = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == implementing_name
        )
        if not implementers:
            return f"Implementing element '{implementing_name}' not found"
        implementer = next(iter(implementers))
        
        # Find interface
        interfaces = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == interface_name
        )
        if not interfaces:
            return f"Interface '{interface_name}' not found"
        interface = next(iter(interfaces))
        
        # Create realization
        realization = element_factory.create(UML.InterfaceRealization)
        realization.implementingClassifier = implementer
        realization.contract = interface
        
        logger.info(f"Created realization: '{implementing_name}' implements '{interface_name}'")
        return f"Created realization: '{implementing_name}' implements '{interface_name}'"
    except Exception as e:
        logger.error(f"Error creating realization: {e}")
        return f"Error creating realization: {e}"


@mcp.tool()
def create_composition(owner_name: str, part_name: str) -> str:
    """Create a composition relationship (strong ownership).
    
    NOTE: This function is NOT FULLY VALIDATED. Based on documentation examples.
    
    Args:
        owner_name: Name of the owner class
        part_name: Name of the part class
    """
    try:
        # Find owner
        owners = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == owner_name
        )
        if not owners:
            return f"Owner element '{owner_name}' not found"
        owner = next(iter(owners))
        
        # Find part
        parts = element_factory.select(
            lambda e: hasattr(e, "name") and e.name == part_name
        )
        if not parts:
            return f"Part element '{part_name}' not found"
        part = next(iter(parts))
        
        # Create association with composition
        association = element_factory.create(UML.Association)
        
        # Create association ends
        owner_end = element_factory.create(UML.Property)
        owner_end.aggregation = "composite"  # Composition
        owner_end.type = owner
        association.memberEnd = owner_end
        
        part_end = element_factory.create(UML.Property)
        part_end.type = part
        association.memberEnd = part_end
        
        logger.info(f"Created composition: '{owner_name}' *-- '{part_name}'")
        return f"Created composition: '{owner_name}' *-- '{part_name}'"
    except Exception as e:
        logger.error(f"Error creating composition: {e}")
        return f"Error creating composition: {e}"


@mcp.tool()
def add_operation_to_class(class_name: str, operation_name: str, return_type: str = "") -> str:
    """Add an operation (method) to a class.
    
    NOTE: This function is NOT FULLY VALIDATED. Based on documentation examples.
    
    Args:
        class_name: Name of the class
        operation_name: Name of the operation (e.g., "createStudy(name, objectId): StudyId")
        return_type: Optional return type
    """
    try:
        # Find class
        classes = element_factory.select(
            lambda e: isinstance(e, UML.Class) and hasattr(e, "name") and e.name == class_name
        )
        if not classes:
            return f"Class '{class_name}' not found"
        cls = next(iter(classes))
        
        # Create operation
        operation = element_factory.create(UML.Operation)
        operation.name = operation_name
        
        # Parse operation name for return type if provided
        if ":" in operation_name:
            parts = operation_name.split(":")
            operation.name = parts[0].strip()
            if len(parts) > 1:
                return_type = parts[1].strip()
        
        if return_type:
            # Try to find return type class, or use typeValue
            return_types = element_factory.select(
                lambda e: hasattr(e, "name") and e.name == return_type
            )
            if return_types:
                operation.type = next(iter(return_types))
            else:
                # Use typeValue for primitive types
                param = element_factory.create(UML.Parameter)
                param.direction = "return"
                param.typeValue = return_type
                operation.ownedParameter = param
        
        cls.ownedOperation = operation
        
        logger.info(f"Added operation '{operation_name}' to class '{class_name}'")
        return f"Added operation '{operation_name}' to class '{class_name}'"
    except Exception as e:
        logger.error(f"Error adding operation: {e}")
        return f"Error adding operation: {e}"


@mcp.tool()
def create_comment(text: str, diagram_name: str = None) -> str:
    """Create a comment (note) in the model.
    
    NOTE: This function is NOT FULLY VALIDATED. Based on documentation examples.
    
    Args:
        text: Text content of the comment
        diagram_name: Optional diagram name to add comment to
    """
    try:
        comment = element_factory.create(UML.Comment)
        comment.body = text
        
        if diagram_name:
            diagrams = element_factory.select(
                lambda e: isinstance(e, Diagram) and hasattr(e, "name") and e.name == diagram_name
            )
            if diagrams:
                diagram = next(iter(diagrams))
                from gaphor.diagram.drop import drop
                drop(comment, diagram, 0, 0)
        
        logger.info(f"Created comment with text: {text[:50]}...")
        return f"Created comment (id: {comment.id})"
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        return f"Error creating comment: {e}"


def main():
    mcp.run()
    return 0
