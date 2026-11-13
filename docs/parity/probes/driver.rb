#!/usr/bin/env ruby
# frozen_string_literal: true
# Parity battery driver (ruby leg).
# Usage: ruby driver.rb <maps_dir> <map_id> <input> [--stage S] [--lang L] [--reverse] [--each]
# Prints:  OK<TAB>result   or   ERR<TAB>Class<TAB>message
$LOAD_PATH.unshift File.expand_path("~/src/interscript/interscript-ruby-wf1/lib")
require "interscript"

maps_dir, map_id, input = ARGV[0], ARGV[1], ARGV[2]
rest = (ARGV[3..] || []).dup
stage = "main"
language = nil
reverse = false
each_mode = false
until rest.empty?
  arg = rest.shift
  case arg
  when "--stage"   then stage = rest.shift
  when "--lang"    then language = rest.shift
  when "--reverse" then reverse = true
  when "--each"    then each_mode = true
  else abort "unknown flag #{arg}"
  end
end

Interscript.load_path.unshift(maps_dir)

begin
  doc = Interscript.parse(map_id)
  out =
    if reverse
      rdoc = doc.reverse
      Interscript::Interpreter.call(rdoc).call(input, :main)
    else
      interp = Interscript::Interpreter.call(map_id)
      if each_mode
        interp.call(input, stage.to_sym, each: true, language: language).to_a.join("|")
      else
        interp.call(input, stage.to_sym, language: language)
      end
    end
  puts "OK\t#{out}"
rescue Exception => e # rubocop:disable Lint/RescueException -- battery wants every failure shape
  msg = (e.message || "").lines.first.to_s.chomp
  puts "ERR\t#{e.class.name}\t#{msg}"
end
