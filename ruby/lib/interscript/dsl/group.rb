class Interscript::DSL::Group

  include Interscript::DSL::Items

  attr_accessor :node

  def initialize(&block)
    @node = Interscript::Node::Group.new
    self.instance_exec(&block)
    @node

  end

  def map(*args)
    {}
  end

  def run(*args)
    nil
  end

  def sub(from, to, **kargs, &block)
    puts "sub(#{from.inspect},#{to}, kargs = #{
      kargs.inspect
    }) from #{self.inspect}" if $DEBUG

    rule = Interscript::Node::Rule::Sub.new(from, to,**kargs)
    @node.children << rule
  end

  def any(chars)
    puts "any(#{chars.inspect}) from #{self.inspect}" if $DEBUG
    Interscript::Node::Item::Any.new(chars)
  end

  def parallel(&block)
    puts "parallel(#{chars.inspect}) from #{self.inspect}" if $DEBUG
    group = Interscript::DSL::Group::Parallel.new(&block)
    @node.children << group.node
  end

end

require 'interscript/dsl/group/parallel'