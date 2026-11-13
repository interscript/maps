#!/usr/bin/env bash
# Corpus parse timing: parse all 428 corpus maps, in-process timing, 3 runs.
# Usage: time-ruby.sh
ruby -I/Users/mulgogi/src/interscript/interscript-ruby-wf1/lib -e '
require "interscript"
files = Dir["/Users/mulgogi/src/interscript/maps/maps/*.isc"].sort
abort "no files" if files.empty?
3.times do
  t0 = Process.clock_gettime(Process::CLOCK_MONOTONIC)
  ok = 0
  files.each do |f|
    begin
      Interscript::Interpreter.parse_isc(f)
      ok += 1
    rescue => e
      warn "FAIL #{File.basename(f)}: #{e.message.lines.first}"
    end
  end
  t1 = Process.clock_gettime(Process::CLOCK_MONOTONIC)
  puts format("ruby parse %d/%d maps in %.1f ms", ok, files.size, (t1 - t0) * 1000)
end
# startup baseline: require + no parse
t0 = Process.clock_gettime(Process::CLOCK_MONOTONIC)
Interscript::Interpreter.parse_isc(files.first)
t1 = Process.clock_gettime(Process::CLOCK_MONOTONIC)
puts format("ruby first-map warm parse: %.1f ms", (t1 - t0) * 1000)
'
