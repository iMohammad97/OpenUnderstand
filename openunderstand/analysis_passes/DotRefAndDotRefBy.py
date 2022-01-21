"""
## Description
This module find all OpenUnderstand import demand and importby demand references in a Java project


## References


"""

__author__ = 'Mohammad Mohammadi'
__version__ = '0.1.0'

from db.models import EntityModel, KindModel
from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaParserLabeledListener import JavaParserLabeledListener


class DotRefAndDotRefBy(JavaParserLabeledListener):

    def __init__(self, file_name, name, content):
        self.dot_ref = []
        self.dot_ref_by = []
        self.dot_ref_found = False
        self.file_name = file_name
        self.name = name
        self.content = content
        java_file_kind = KindModel.get_or_none(is_ent_kind=True, _name="Java File")
        self.ent_file = EntityModel.get_or_none(_kind=java_file_kind, _name=name, _longname=file_name)
        if self.ent_file is None:
            EntityModel.get_or_create(_kind=java_file_kind, _name=name, _longname=file_name,
                                      _contents=content)
            print("Add File Entity " + name)
            self.ent_file = EntityModel.get_or_none(_kind=java_file_kind, _name=name, _longname=file_name)
        else:
            self.ent_file._contents = content
            self.ent_file.save()

    def enterMethodDeclaration(self, ctx: JavaParserLabeled.MethodDeclarationContext):
        if '.' in ctx.getText():
            self.dot_ref.append((ctx.IDENTIFIER().getText(), ctx.start.line, ctx.start.column))
            self.dot_ref_found = True


    def enterExpression0(self, ctx: JavaParserLabeled.Expression0Context):
        if self.dot_ref_found:
            self.dot_ref_by.append((ctx.getText(), ctx.start.line, ctx.start.column))

            java_unknown_package_kind = KindModel.get_or_none(is_ent_kind=True, _name="Java Unknown Package")
            ent = EntityModel.get_or_none(_name=self.name, _longname=self.file_name)
            if ent is None:
                EntityModel.get_or_create(_kind=java_unknown_package_kind, _parent=self.ent_file._id,
                                          _name=self.name, _longname=self.file_name,
                                          _contents='')
