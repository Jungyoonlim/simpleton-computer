from fileio.files import load_doc, load_mixed, print_list

_, doc_v = load_doc("examples/sample_mixed_content.txt")
vals = load_mixed(doc_v.path)
print_list(vals)
