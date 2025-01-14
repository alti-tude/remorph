package com.databricks.labs.remorph.parsers

import org.antlr.v4.runtime.tree.ParseTree

trait ParserCommon {
  protected def occursBefore(a: ParseTree, b: ParseTree): Boolean =
    a.getSourceInterval.startsBeforeDisjoint(b.getSourceInterval)
}
