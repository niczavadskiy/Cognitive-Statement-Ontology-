# Bias-oriented Notation

## Purpose

The bias-oriented notation focuses on cognitive biases and their influence on statements. It helps:
- Identify patterns of cognitive biases
- Show how biases affect multiple statements
- Understand the relationships between different biases

## Key Features

1. **Bias-centric Structure**
   - Biases are the central nodes in the graph
   - Statements are connected to the biases that influenced them
   - Multiple statements can be connected to a single bias

2. **Bias Relationships**
   - Biases can be connected to each other
   - Shows how one bias can lead to another
   - Helps identify patterns of cognitive distortion

3. **Visualization**
   - Biases are shown as central nodes
   - Statements are connected to relevant biases
   - Bias relationships are shown through edges
   - Statement clusters show bias influence patterns

## Use Cases

- Analyzing cognitive bias patterns
- Identifying bias clusters
- Understanding bias relationships
- Mapping bias influence on reasoning

## Example

```json
{
  "biases": [
    {
      "id": "b1",
      "name": "confirmation_bias",
      "statements": ["s1", "s2"],
      "related_biases": ["b2"]
    },
    {
      "id": "b2",
      "name": "anchoring_bias",
      "statements": ["s2", "s3"],
      "related_biases": ["b1"]
    }
  ],
  "statements": [
    {
      "id": "s1",
      "text": "This evidence supports my theory",
      "biases": ["b1"]
    },
    {
      "id": "s2",
      "text": "The first study I found confirms this",
      "biases": ["b1", "b2"]
    },
    {
      "id": "s3",
      "text": "This number seems reasonable based on that",
      "biases": ["b2"]
    }
  ]
}
```

## Visualization

The bias-oriented notation is particularly useful for:
- Showing bias influence patterns
- Identifying bias clusters
- Understanding bias relationships
- Mapping cognitive distortion patterns

## Описание
Искажение-ориентированная нотация представляет данные с фокусом на когнитивных искажениях, где:
- Каждое искажение представлено в виде отдельного блока
- Утверждения размещаются внутри блоков соответствующих искажений
- Связи между искажениями отображаются через общие утверждения и прямые связи между искажениями

## Визуальные элементы

### Узлы
- **Когнитивные искажения**: 
  - Отображаются в виде цветных блоков
  - Каждому искажению присваивается уникальный пастельный цвет из набора из 12 цветов
  - При количестве искажений более 12 цвета повторяются по кругу
  - Заголовок искажения отображается в верхней части блока
- **Утверждения**: 
  - Отображаются только те утверждения которые имеют связь с Когнитивным(и) искажением(ями)
  - Размещаются внутри блоков искажений
  - Если утверждение связано с несколькими искажениями, оно отображается в каждом соответствующем блоке
  - Утверждения в данной нотации не имеют цветового отображения задаваемого в зависимости от достоверности

### Связи
- Толстые линии между блоками искажений
- Числовые метки на линиях показывают:
  - Общее количество связей (верхняя строка)
  - Разбивку связей в скобках (нижняя строка):
    * Количество общих утверждений
    * Количество прямых связей между искажениями
- Пример метки:
  ```
  5
  (3+2)
  ```
  где:
  - 5 - общее количество связей
  - 3 - количество общих утверждений
  - 2 - количество прямых связей между искажениями
- Связи не имеют направлений

## Особенности
- Компактное представление каждого искажения
- Четкое отображение связей между искажениями
- Визуализация силы связей через числовые метки
- Возможность проследить влияние аргументов на утверждения
- Детальное представление типов связей между искажениями

## Использование
```sh
python tools/render_graph.py <input_file> bias
```

## Пример
![Пример искажение-ориентированной нотации](cognitive_ontology_graph_bias.png) 