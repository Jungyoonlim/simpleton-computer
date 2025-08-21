## Run the demo

```bash
python -m examples.demo
```

### Expected output:

```txt
Extracted comments: [CommentValue(author='joanne', date='2025-08-10', text='Fix this paragraph', source_path='examples/sample.txt'), CommentValue(author='alice', date='2025-08-15', text='Consider shortening intro', source_path='examples/sample.txt'), CommentValue(author='bob', date='2025-08-05', text='Add citation here', source_path='examples/sample.txt')]
Plan trace: ['extract_comments']
Final value: [CommentValue(author='joanne', date='2025-08-10', text='Fix this paragraph', source_path='examples/sample.txt'), CommentValue(author='alice', date='2025-08-15', text='Consider shortening intro', source_path='examples/sample.txt'), CommentValue(author='bob', date='2025-08-05', text='Add citation here', source_path='examples/sample.txt')]

Option 1: Explicit delete_all
[delete_all] Would delete 3 comments from examples/sample.txt

Option 3: Get single comment
First comment (Option[Comment]): CommentValue(author='joanne', date='2025-08-10', text='Fix this paragraph', source_path='examples/sample.txt')
```