export async function processQuery(query, textResponseElement, imageResponseElement) {
    try {
        // Enhanced mock responses with more detailed content
        const responses = {
            "Tell me about artificial intelligence": {
                text: "Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines that can simulate human-like thinking and behavior. Key areas include machine learning, neural networks, and natural language processing.",
                image: "https://images.unsplash.com/photo-1535303311164-1bbe6cfab5d4?auto=format&fit=crop&q=80&w=600&h=400"
            },
            "Describe a beautiful sunset": {
                text: "A breathtaking sunset paints the sky with a mesmerizing palette of warm oranges, deep crimsons, and soft purples. The sun gently descends, casting long shadows and transforming the landscape into a canvas of ethereal beauty.",
                image: "https://images.unsplash.com/photo-1508615263927-c4c2d6a4de1c?auto=format&fit=crop&q=80&w=600&h=400"
            },
            "Create an image of a futuristic city": {
                text: "Imagine a gleaming metropolis with towering skyscrapers of glass and steel, interconnected by transparent skywalks, and hovering electric vehicles weaving between buildings illuminated by dynamic holographic displays.",
                image: "https://images.unsplash.com/photo-1581777814039-09cbfb9f8cdc?auto=format&fit=crop&q=80&w=600&h=400"
            }
        };

        // Default fallback for unknown queries
        const defaultResponse = {
            text: "I apologize, but I don't have a specific response for that query. Could you try rephrasing or asking something more specific?",
            image: "https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&q=80&w=600&h=400"
        };

        // Select response
        const response = responses[query] || defaultResponse;

        // Update Text Response
        textResponseElement.innerHTML = `
            <div class="p-3">
                <p class="lead">${response.text}</p>
            </div>
        `;

        // Update Image Response
        imageResponseElement.innerHTML = `
            <img src="${response.image}" alt="Generated Response" class="img-fluid rounded shadow-sm">
        `;

    } catch (error) {
        console.error('Query processing error:', error);
        textResponseElement.innerHTML = `
            <div class="text-danger p-3">
                <p>Sorry, an error occurred while processing your query.</p>
            </div>
        `;
    }
}