#!/usr/bin/env ruby
# frozen_string_literal: true
# Fuzz driver (ruby leg). Usage: ruby driver-ruby.rb <case.isc> <inputs-json>
# Prints a single JSON line:
#   {"runtime":"ruby","parse":{...},"exec":[...],"ms":N}
#
# Parse leg: the .isc DSL load path (Interscript.parse by filename stem),
# the reference entry for ruby. Exec leg: Interscript::Interpreter#call over
# the main stage, per input. Every failure is captured and bucketed; a
# nonzero process exit means the VM itself died (a crash finding).

require "json"

$LOAD_PATH.unshift(ENV["RUBY_LIB"] || File.expand_path("../../interscript-ruby/lib", __dir__))
require "interscript"

# Bucket map (canonical buckets: OK PARSE LOAD LOGIC UNSUPPORTED CRASH OTHER).
CRASH_CLASSES = %w[
  ArgumentError NoMethodError TypeError NameError KeyError IndexError
  RangeError RegexpError FrozenError RuntimeError NotImplementedError
  SystemStackError LocalJumpError ZeroDivisionError FloatDomainError
  EOFError IOError ScriptError LoadError NoMatchingPatternError
].freeze

def bucket(e)
  name = e.class.name.to_s
  case name
  when "Interscript::Isc::ParseError"      then "PARSE"
  when "Interscript::MapNotFoundError"     then "LOAD"
  when "Interscript::SystemConversionError",
       "Interscript::MapLogicError"        then "LOGIC"
  when "Interscript::ExternalUtilError"    then "UNSUPPORTED"
  when *CRASH_CLASSES                      then "CRASH"
  else "OTHER"
  end
end

def err_shape(e)
  {
    status: "ERR",
    class: e.class.name.to_s,
    bucket: bucket(e),
    message: ((e.message || "").lines.first || "").to_s[0, 200],
  }
end

case_file = ARGV[0]
inputs = JSON.parse(ARGV[1] || "[]")
dir = File.dirname(File.expand_path(case_file))
stem = File.basename(case_file, ".isc")
result = { "runtime" => "ruby" }

Interscript.load_path.unshift(dir)
begin
  Interscript.parse(stem)
  result["parse"] = { "status" => "OK" }
  interp = Interscript::Interpreter.call(stem)
  result["exec"] = inputs.map do |input|
    begin
      { "input" => input, "status" => "OK", "output" => interp.call(input, :main) }
    rescue Exception => e # rubocop:disable Lint/RescueException -- every failure shape is data here
      { "input" => input }.merge(err_shape(e))
    end
  end
rescue Exception => e # rubocop:disable Lint/RescueException
  result["parse"] = err_shape(e)
end

puts JSON.generate(result)
