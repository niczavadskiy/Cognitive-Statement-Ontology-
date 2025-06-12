# Sequential Notation

## Purpose

The sequential notation is designed to represent the logical flow of reasoning, showing how statements lead to conclusions. It helps:
- Track the progression of arguments
- Identify logical connections between statements
- Show how biases influence the reasoning chain

## Key Features

1. **Statement Chain**
   - Statements are connected in a directed graph
   - Each statement can lead to one or more conclusions
   - The chain shows the logical progression of reasoning

2. **Bias Connections**
   - Biases are connected to statements they influenced
   - Multiple biases can affect a single statement
   - Bias connections show where reasoning might be flawed

3. **Visualization**
   - Statements are shown as nodes
   - Directed edges show logical connections
   - Undirected edges show bias influences
   - The final node represents the main conclusion

## Use Cases

- Analyzing argument structure
- Identifying logical fallacies
- Tracking reasoning patterns
- Evaluating argument validity

## Example

```json
{
  "statements": [
    {
      "id": "s1",
      "text": "If it rains, the ground will be wet",
      "leads_to": ["s2"],
      "biases": []
    },
    {
      "id": "s2",
      "text": "The ground is wet",
      "leads_to": ["s3"],
      "biases": ["post_hoc"]
    },
    {
      "id": "s3",
      "text": "Therefore, it rained",
      "leads_to": [],
      "biases": ["post_hoc"]
    }
  ]
}
```

## Visualization

The sequential notation is particularly useful for:
- Showing the logical flow of arguments
- Identifying gaps in reasoning
- Highlighting where biases affect conclusions
- Mapping complex argument structures

## Описание
Последовательная нотация представляет данные в виде цепочки взаимосвязанных элементов, где:
- Утверждения (statements) отображаются в виде прямоугольников
- Когнитивные искажения (biases) представлены в виде шестиугольников
- Аргументы (arguments) отображаются в виде сиреневых кругов
- Все элементы соединены направленными связями, показывающими логическую последовательность

## Визуальные элементы

### Узлы
- **Утверждения**: 
  - Отображаются в виде прямоугольников
  - Цвет зависит от достоверности (credibility):
    - Красный: неверное утверждение
    - Желтый: спорное утверждение
    - Зеленый: верное утверждение
    - Серый: неопределенная достоверность
- **Когнитивные искажения**: 
  - Отображаются в виде шестиугольников
  - Имеют единый цвет для всех искажений
- **Аргументы**:
  - Отображаются в виде сиреневых кругов
  - Имеют фиксированный размер для компактности

### Связи
- Направленные линии со стрелками
- Каждая связь имеет метку, указывающую тип отношения
- Связи показывают логическую последовательность от утверждений через искажения к аргументам

## Особенности
- Четкое отображение логической последовательности
- Визуальное различие типов элементов через форму и цвет
- Направленные связи для понимания причинно-следственных отношений
- Компактное представление аргументов

## Использование
```sh
python tools/render_graph.py <input_file> sequential
```

## Пример
![Пример последовательной нотации](cognitive_ontology_graph_sequential.png) 