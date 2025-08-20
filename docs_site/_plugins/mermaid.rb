# Custom Jekyll plugin to convert mermaid code blocks to div tags
# This allows mermaid.js to render diagrams on GitHub Pages

module Jekyll
  class MermaidBlockConverter
    def self.convert(content)
      return content unless content.include?('```mermaid')
      
      # Convert ```mermaid...``` to <pre class="mermaid">...</pre>
      # More robust regex that handles various newline scenarios
      content.gsub(/```mermaid\s*\n(.*?)\n\s*```/m) do
        mermaid_code = $1.strip
        %(<pre class="mermaid">\n#{mermaid_code}\n</pre>)
      end
    end
  end
end

# Register hooks to process content before rendering
Jekyll::Hooks.register :documents, :pre_render do |document|
  if document.output_ext == ".html"
    document.content = Jekyll::MermaidBlockConverter.convert(document.content)
  end
end

Jekyll::Hooks.register :pages, :pre_render do |page|
  if page.output_ext == ".html"
    page.content = Jekyll::MermaidBlockConverter.convert(page.content)
  end
end

