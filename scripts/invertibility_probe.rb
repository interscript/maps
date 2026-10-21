require "interscript"
require "json"

maps = Interscript.maps
result = { "generated" => Time.now.utc.iso8601, "runtime" => Interscript::VERSION,
           "pairs" => [], "injectivity" => {} }

# 1) explicit reverse pairs: round-trip the forward map's embedded tests
maps.each do |m|
  next unless m =~ /\A([a-z0-9]+-[a-z0-9]+)-(\w+)-(\w+)-(.+)\z/
  rev = "#{$1}-#{$3}-#{$2}-#{$4}"
  next unless maps.include?(rev)
  begin
    parsed = Interscript.parse(m)
    tests = (parsed.tests&.data || []).map(&:first).compact
    next if tests.empty?
    passed = 0; failed = []
    tests.each do |src|
      begin
        rt = Interscript.transliterate(rev, Interscript.transliterate(m, src))
        if rt == src then passed += 1 else failed << {src: src, rt: rt} end
      rescue => e
        failed << {src: src, error: e.message[0,80]}
      end
    end
    result["pairs"] << { map: m, reverse: rev, tests: tests.size,
                         roundtrip: passed, failed_count: failed.size,
                         failures: failed.first(3) }
  rescue => e
    result["pairs"] << { map: m, error: e.message[0,80] }
  end
end

# 2) injectivity probe on every map's embedded tests
maps.each do |m|
  begin
    parsed = Interscript.parse(m)
    tests = (parsed.tests&.data || []).map(&:first).compact
    next if tests.empty?
    outs = tests.map { |t| Interscript.transliterate(m, t) }
    coll = tests.size - outs.uniq.size
    result["injectivity"][m] = { tests: tests.size, collisions: coll }
  rescue => e
    result["injectivity"][m] = { error: e.message[0,60] }
  end
end

File.write("/tmp/a2-ledger.json", JSON.pretty_generate(result))
total_pairs = result["pairs"].size
clean = result["pairs"].count { |p| p[:roundtrip] && p[:failed_count] == 0 }
lossy = result["pairs"].count { |p| p[:failed_count].to_i > 0 }
errs  = result["pairs"].count { |p| p[:error] }
coll  = result["injectivity"].values.count { |v| v[:collisions].to_i > 0 }
puts "reverse pairs: #{total_pairs} (lossless #{clean}, lossy #{lossy}, errors #{errs})"
puts "maps with test-input collisions: #{coll} / #{result['injectivity'].size}"
