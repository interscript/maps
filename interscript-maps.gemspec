INTERSCRIPT_MAPS_VERSION = "2.4.3"

Gem::Specification.new do |spec|
  spec.name          = "interscript-maps"
  spec.version       = INTERSCRIPT_MAPS_VERSION
  spec.summary       = "Interoperable script conversion systems — map data"
  spec.description   = "Map data package for Interscript interoperable script conversion systems."
  spec.authors       = ["Ribose Inc."]
  spec.email         = ["open.source@ribose.com"]

  spec.homepage      = "https://www.interscript.com"
  spec.license       = "MIT"
  spec.required_ruby_version = ">= 3.3.0"

  spec.metadata["homepage_uri"]    = spec.homepage
  spec.metadata["source_code_uri"] = "https://github.com/interscript/maps"
  spec.metadata["changelog_uri"]   = "https://github.com/interscript/maps/releases"
  spec.metadata["bug_tracker_uri"] = "https://github.com/interscript/maps/issues"
  spec.metadata["rubygems_mfa_required"] = "true"

  spec.files = Dir.chdir(__dir__) do
    Dir[
      "libs/**/*",
      "maps/**/*",
      "maps-staging/**/*",
      "interscript-maps.yaml",
      "README*",
      "LICENSE*",
      "*.gemspec"
    ].select { |f| File.file?(f) }
  end
  spec.require_paths = [""]
end
