"""Helpers for generating Java/Xtencil code blocks from parsed Items and scenarios."""

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from application.spreadsheet_parser import Item, SourcingGroup, SourceFromTLIPath
from application.tommm_parser import InboundDocScenario


# ---------------------------- TLI fields (FIELDDEF) ----------------------------

# Base templates are copied from the original poRsxRead.xtl/pcRsxRead.xtl
# and then patched per Item. This preserves indentation and attribute ordering.

_SHIPTO_FIELD_TEMPLATE = (
    '        <FIELDDEF calculateType="none" condition="None" dataType="JString" display="Y" '
    'dtdRequired="N" edi="Y" editable="Y" enable="Y" exclude="N" freeFormable="Y" '
    'includeInTestFile="Y" insert="N" javaName="ShipToCode" keyType="NONE" '
    'lookupBlankIfNotFound="Y" lookupByFormat="N" lookupByReceiver="N" lookupBySender="N" '
    'lookupEvent="lookupBeforeInit" mandatory="N" maxLength="80" minLength="2" '
    'name="Ship To Location Code" nextRow="N" persistent="Y" present="Y" print="Y" '
    'rounding="2" templatable="Y" useExternalContent="N" workImplemented="N">\n'
    "          <VALIDATION>\n"
    "            <?java //begin init\n"
    "public void init() {\n"
    "\tif (me.hasData()){\n"
    "\t\troot.hasTLILocation = true;\n"
    "\t}\n"
    "}//end-method\n"
    "//end init\n"
    "?>\n"
    "          </VALIDATION>\n"
    "        </FIELDDEF>"
)

_GENERIC_FIELD_TEMPLATE = (
    '        <FIELDDEF calculateType="none" condition="None" dataType="JString" display="Y" '
    'dtdRequired="N" edi="Y" editable="Y" enable="Y" exclude="N" freeFormable="Y" '
    'includeInTestFile="Y" insert="N" javaName="VendorNumber" keyType="NONE" '
    'lookupBlankIfNotFound="Y" lookupByFormat="N" lookupByReceiver="N" lookupBySender="N" '
    'lookupEvent="lookupBeforeInit" mandatory="N" maxLength="30" minLength="1" '
    'name="Vendor Number" nextRow="N" persistent="Y" present="Y" print="Y" '
    'rounding="2" templatable="Y" useExternalContent="N" workImplemented="N"/>'
)


def get_tli_fields_code(items: Iterable[Item]) -> str:
    """Generate FIELDDEF XML for all Items.

    - For N1/04/ST item use ShipToCode template with validation block.
    - For all others use generic single-line FIELDDEF template.
    - javaName, maxLength, minLength, name are taken from Item.
    """

    lines: List[str] = []

    for item in items:
        java_name = (item.tli_tag_850 or "").strip()
        if not java_name:
            continue

        # Fallbacks for min/max/label
        max_len = str(item.spreadsheet_max) if item.spreadsheet_max is not None else "80"
        min_len = str(item.spreadsheet_min) if item.spreadsheet_min is not None else "1"
        label = (item.spreadsheet_label or java_name).replace('"', "'")

        is_special_ship_to = (
            (item.edi_segment or "") == "N1"
            and (item.edi_element_number or "") in {"04", "4"}
            and (item.edi_qualifier or "") == "ST"
        )

        if is_special_ship_to:
            block = _SHIPTO_FIELD_TEMPLATE
            block = block.replace('javaName="ShipToCode"', f'javaName="{java_name}"')
            block = block.replace('maxLength="80"', f'maxLength="{max_len}"')
            block = block.replace('minLength="2"', f'minLength="{min_len}"')
            block = block.replace('name="Ship To Location Code"', f'name="{label}"')
            lines.append(block)
        else:
            line = _GENERIC_FIELD_TEMPLATE
            line = line.replace('javaName="VendorNumber"', f'javaName="{java_name}"')
            line = line.replace('maxLength="30"', f'maxLength="{max_len}"')
            line = line.replace('minLength="1"', f'minLength="{min_len}"')
            line = line.replace('name="Vendor Number"', f'name="{label}"')
            lines.append(line)

    return "\n".join(lines)


# ------------------------ getOrderManagementModel methods ----------------------


def get_850_omm_method_code(scenarios: Iterable[InboundDocScenario]) -> str:
    """Generate body of getOrderManagementModel() for 850 document scenarios."""

    # Group scenarios by key
    by_key: Dict[str, List[InboundDocScenario]] = defaultdict(list)
    for s in scenarios:
        if s.document_number == 850:
            by_key[s.key].append(s)

    lines: List[str] = []
    lines.append("private String getOrderManagementModel() {")
    lines.append("")

    # First, simple (not changed_by_850) scenarios
    for key, group in by_key.items():
        simple = [s for s in group if not s.is_changed_by_850_scenario]
        for s in simple:
            if not s.key or not s.name:
                continue
            lines.append(f"    if (poNumber.equals(\"{s.key}\")) {{")
            lines.append(f"    \treturn \"{s.name}\";")
            lines.append("    }")

    # Then, changed-by-850 pairs (is_changed_by_850_scenario = True)
    for key, group in by_key.items():
        changed = [s for s in group if s.is_changed_by_850_scenario]
        if len(changed) < 2:
            continue
        # Keep input order; only first two are used
        first, second = changed[0], changed[1]
        if not key or not first.tset_code or not second.tset_code:
            continue
        lines.append("")
        lines.append(f"    if (poNumber.equals(\"{key}\")) {{")
        lines.append(f"        if (tsetCode.equals(\"{first.tset_code}\")) {{")
        lines.append(f"            return \"{first.name}\";")
        lines.append("        }")
        lines.append(f"    \telse if (tsetCode.equals(\"{second.tset_code}\")) {{")
        lines.append(f"            return \"{second.name}\";")
        lines.append("        }")
        lines.append("    }")

    lines.append("")
    lines.append("    return null;")
    lines.append("}")

    return "\n".join(lines)


def get_860_omm_method_code(scenarios: Iterable[InboundDocScenario]) -> str:
    """Generate body of getOrderManagementModel() for 860 document scenarios."""

    lines: List[str] = []
    lines.append("private String getOrderManagementModel() {")
    lines.append("")

    for s in scenarios:
        if s.document_number != 860:
            continue
        if not s.key or not s.name:
            continue
        lines.append(f"    if (poNumber.equals(\"{s.key}\")) {{")
        lines.append(f"    \treturn \"{s.name}\";")
        lines.append("    }")

    lines.append("")
    lines.append("    return null;")
    lines.append("}")

    return "\n".join(lines)


# ---------------------------- Populate methods/maps ---------------------------


def _group_items_by_sourcing_group(items: Iterable[Item]) -> Dict[Tuple[Optional[int], str, str], Tuple[SourcingGroup, List[Item]]]:
    """Group Items by unique SourcingGroup.

    Key is (sourcing_group_properties_id, populate_method_name, map_name).
    """

    groups: Dict[Tuple[Optional[int], str, str], Tuple[SourcingGroup, List[Item]]] = {}

    for item in items:
        sg = item.sourcing_group
        if sg is None:
            continue
        key = (sg.sourcing_group_properties_id, sg.populate_method_name, sg.map_name)
        if key not in groups:
            groups[key] = (sg, [])
        groups[key][1].append(item)

    return groups


def get_single_populate_method_code(group: SourcingGroup, items_for_group: Iterable[Item]) -> str:
    """Generate a single populate method body for one SourcingGroup."""

    method_name = group.populate_method_name
    map_name = group.map_name
    lines: List[str] = []
    lines.append(f"void {method_name}() {{")

    for item in items_for_group:
        if not item.tli_tag_850 or not item.rsx_tag_850:
            continue
        lines.append(
            f"    {map_name}.put(\"{item.tli_tag_850}\", \"{item.rsx_tag_850}\");"
        )

    lines.append("}")
    return "\n".join(lines)


def get_populate_methods_code(items: Iterable[Item]) -> str:
    """Generate code for all populate methods for all unique SourcingGroups."""

    groups = _group_items_by_sourcing_group(items)
    method_blocks: List[str] = []

    for (group_id, method_name, map_name), (sg, group_items) in groups.items():
        block = get_single_populate_method_code(sg, group_items)
        if block.strip():
            method_blocks.append(block)

    return "\n\n".join(method_blocks)


def get_populate_maps_code(items: Iterable[Item]) -> str:
    """Generate Java Map declarations for all unique map_name values."""

    groups = _group_items_by_sourcing_group(items)
    unique_map_names = []
    seen = set()

    for (_, _, map_name), (sg, _) in groups.items():
        if map_name and map_name not in seen:
            seen.add(map_name)
            unique_map_names.append(map_name)

    lines = [f"Map<String,String> {name} = new HashMap<String,String>();" for name in unique_map_names]
    return "\n".join(lines)


def get_call_populate_methods_code(items: Iterable[Item]) -> str:
    """Generate Java code calling all unique populate methods."""

    groups = _group_items_by_sourcing_group(items)
    unique_method_names: List[str] = []
    seen = set()

    for (_, method_name, _), (sg, _) in groups.items():
        if method_name and method_name not in seen:
            seen.add(method_name)
            unique_method_names.append(method_name)

    lines = [f"    {name}();" for name in unique_method_names]
    return "\n".join(lines)


# ---------------------- sourceFromTLI structure & wrappers --------------------


def get_source_from_tli_structure_dictionary(
    items: Iterable[Item],
) -> Dict[SourceFromTLIPath, List[SourcingGroup]]:
    """Build mapping: SourceFromTLIPath -> unique SourcingGroup list.

    For all existing Item instances, collect SourcingGroup objects that have a
    non-empty ``source_from_tli_path`` attached. The result is a dictionary
    where:

    - key: unique ``SourceFromTLIPath`` (dataclass is frozen & hashable)
    - value: list of unique ``SourcingGroup`` objects that reference this path

    Uniqueness of SourcingGroup within a single path is determined by
    ``(sourcing_group_properties_id, populate_method_name, map_name)`` so that
    the same logical group referenced by multiple Items is returned only once.
    """

    structure: Dict[SourceFromTLIPath, List[SourcingGroup]] = {}
    seen_per_path: Dict[SourceFromTLIPath, set] = {}

    for item in items:
        sg = item.sourcing_group
        if sg is None:
            continue

        path = sg.source_from_tli_path
        if path is None:
            continue

        if path not in structure:
            structure[path] = []
            seen_per_path[path] = set()

        key = (
            sg.sourcing_group_properties_id,
            sg.populate_method_name,
            sg.map_name,
        )

        if key not in seen_per_path[path]:
            seen_per_path[path].add(key)
            structure[path].append(sg)

    return structure

