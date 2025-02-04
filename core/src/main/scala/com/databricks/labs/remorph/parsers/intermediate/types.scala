package com.databricks.labs.remorph.parsers.intermediate

abstract class DataType
case class NullType() extends DataType
case class BooleanType() extends DataType
case class BinaryType() extends DataType

// Numeric types
case class ByteType() extends DataType
case class ShortType() extends DataType
case class IntegerType() extends DataType
case class LongType() extends DataType

case class FloatType() extends DataType
case class DoubleType() extends DataType
case class DecimalType() extends DataType

// String types
case class StringType() extends DataType
case class CharType() extends DataType
case class VarCharType() extends DataType

// Datatime types
case class DateType() extends DataType
case class TimestampType() extends DataType
case class TimestampNTZType() extends DataType

// Interval types
case class CalendarIntervalType() extends DataType
case class YearMonthIntervalType() extends DataType
case class DayTimeIntervalType() extends DataType

// Complex types
case class ArrayType() extends DataType
case class StructType() extends DataType
case class MapType() extends DataType

// UserDefinedType
case class UDTType() extends DataType

// UnparsedDataType
case class UnparsedType() extends DataType