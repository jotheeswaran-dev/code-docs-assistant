require "json"

ROOT = "/tmp"

module Store
  DEFAULT = 1

  class Entry
    def initialize(name)
      @name = name
    end

    def self.build(name)
      new(name)
    end
  end
end

def top_level(value)
  value
end
