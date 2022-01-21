"""
Open Understand main driver
to create project parse tree, analyze project, and create symbol table db
It is the same Understand und command line tool

"""
import os
from pprint import pprint

from antlr4 import FileStream, CommonTokenStream, ParseTreeWalker

from analysis_passes.DotRefAndDotRefBy import DotRefAndDotRefBy
from db.api import open as db_open, create_db, Kind
from db.fill import main
from db.models import ProjectModel, EntityModel, KindModel, ReferenceModel
from gen.javaLabeled.JavaLexer import JavaLexer
from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled


class Project:

    def start_analyze(self, project_address):
        self.dot_ref = []
        self.dot_ref_by = []

        for root, dirs, files in os.walk(project_address):
            for file in files:
                if file.endswith('.java'):
                    address = os.path.join(root, file)
                    try:
                        stream = FileStream(address)
                    except:
                        print(file, 'can not read')
                        continue
                    lexer = JavaLexer(stream)
                    tokens = CommonTokenStream(lexer)
                    parser = JavaParserLabeled(tokens)
                    tree = parser.compilationUnit()
                    listener = DotRefAndDotRefBy(address, file, stream.strdata)
                    walker = ParseTreeWalker()
                    walker.walk(
                        listener=listener,
                        t=tree
                    )
                    if (len(listener.dot_ref) > 0) and (len(listener.dot_ref_by) > 0):
                        self.dot_ref.append((listener.ent_file, listener.dot_ref, listener.dot_ref_by))
                        self.dot_ref_by.append((listener.ent_file, listener.dot_ref, listener.dot_ref_by))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    create_db("database", "/")
    db = db_open("database")
    p = Project()
    root = ProjectModel.get_or_none().root
    print(root)
    print("Start Analyze Entity (Package and File)")
    print("...........")
    p.start_analyze(root)
    print("...........")
    print("End Analyze Entity (Package and File)")
    print("---------------------------------------")
    # Add References
    print("Start Analyze Reference (DotRef and DotRefBy)")
    print("...........")
    java_unknown_package_kind = KindModel.get_or_none(is_ent_kind=True, _name="Java Unknown Package")
    # java_import_demand = KindModel.get_or_none(is_ent_kind=False, _name="Java Import Demand")
    # java_importby_demand = KindModel.get_or_none(is_ent_kind=False, _name="Java Importby Demand")
    for dot_ref in p.dot_ref:
        dot_ref_package = dot_ref[1]
        dot_ref_by_package = dot_ref[2]
        ent = EntityModel.get_or_none(_longname=dot_ref_package[0])
        ent_by = EntityModel.get_or_none(_longname=dot_ref_by_package[0])
        if ent is None:
            name = dot_ref_package[0]

            EntityModel.get_or_create(_kind=java_unknown_package_kind, _parent=dot_ref[0]._id, _name=name,
                                      _longname=dot_ref_package[0],
                                      _contents='')
            print("Add Package Unknown Entity " + dot_ref_package[0])
            ent = EntityModel.get_or_none(_longname=dot_ref_package[0])

        if ent_by is None:
            name = dot_ref_by_package[0]

            EntityModel.get_or_create(_kind=java_unknown_package_kind, _parent=dot_ref[0]._id, _name=name,
                                      _longname=dot_ref_by_package[0],
                                      _contents='')
            print("Add Package Unknown Entity " + dot_ref_by_package[0])
            ent_by = EntityModel.get_or_none(_longname=dot_ref_by_package[0])

        ref = ReferenceModel.get_or_none(_kind=java_unknown_package_kind, _file=dot_ref[0], _ent=ent,
                                         _scope=dot_ref[0])
        if ref is None:
            ReferenceModel.get_or_create(_kind=java_unknown_package_kind, _file=dot_ref[0], _line=dot_ref_package[1],
                                         _column=dot_ref_package[2], _ent=ent,
                                         _scope=dot_ref[0])
            print("Add DotRef Reference in " + dot_ref[0]._name + " by " + ent._longname)
        else:
            ref._line = dot_ref_package[1]
            ref._column = dot_ref_package[2]
            ref.save()

        ref = ReferenceModel.get_or_none(_kind=java_unknown_package_kind, _file=dot_ref[0], _ent=dot_ref[0],
                                         _scope=ent)
        if ref is None:
            ReferenceModel.get_or_create(_kind=java_unknown_package_kind, _file=dot_ref[0], _line=dot_ref_by_package[1],
                                         _column=dot_ref_by_package[2], _ent=dot_ref[0],
                                         _scope=ent)
            print("Add DotRefBy Reference in " + dot_ref[0]._name + " by " + ent._longname)
        else:
            ref._line = dot_ref_by_package[1]
            ref._column = dot_ref_by_package[2]
            ref.save()
    print("...........")
    print("Stop Analyze Reference (ImportDemand and ImportByDemand)")
