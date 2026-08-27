# Minimal gem tasks for rubygems/release-gem, which runs `rake build` then
# `rake release`. Hand-rolled because bundler/gem_tasks' release task also
# creates and pushes a git tag, which conflicts with the existing v* tags
# this repo cuts for the maps release artifacts.
task :build do
  sh "gem build interscript-maps.gemspec"
end

task release: :build do
  gem_file = Dir["interscript-maps-*.gem"].sort.last
  sh "gem push #{gem_file}"
end
