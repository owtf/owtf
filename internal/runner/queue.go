package runner

import (
	"context"
	"sync"
)

// taskQueue is a deduplicated FIFO whose pending entries can be removed or
// reordered without disturbing tasks from another session.
type taskQueue struct {
	mu      sync.Mutex
	ids     []string
	present map[string]bool
	wake    chan struct{}
}

func newTaskQueue() *taskQueue {
	return &taskQueue{present: make(map[string]bool), wake: make(chan struct{}, 1)}
}

func (q *taskQueue) push(ids []string) {
	q.mu.Lock()
	for _, id := range ids {
		if id == "" || q.present[id] {
			continue
		}
		q.present[id] = true
		q.ids = append(q.ids, id)
	}
	hasWork := len(q.ids) != 0
	q.mu.Unlock()
	if hasWork {
		q.notify()
	}
}

func (q *taskQueue) pop(ctx context.Context) (string, bool) {
	for {
		q.mu.Lock()
		if len(q.ids) != 0 {
			id := q.ids[0]
			q.ids = q.ids[1:]
			delete(q.present, id)
			more := len(q.ids) != 0
			q.mu.Unlock()
			if more {
				q.notify()
			}
			return id, true
		}
		q.mu.Unlock()
		select {
		case <-q.wake:
		case <-ctx.Done():
			return "", false
		}
	}
}

func (q *taskQueue) remove(id string) {
	q.mu.Lock()
	defer q.mu.Unlock()
	if !q.present[id] {
		return
	}
	delete(q.present, id)
	for index, queued := range q.ids {
		if queued == id {
			q.ids = append(q.ids[:index], q.ids[index+1:]...)
			return
		}
	}
}

func (q *taskQueue) reorder(ids []string) {
	q.mu.Lock()
	defer q.mu.Unlock()
	wanted := make(map[string]bool, len(ids))
	ordered := make([]string, 0, len(ids))
	for _, id := range ids {
		if q.present[id] {
			wanted[id] = true
			ordered = append(ordered, id)
		}
	}
	next := 0
	for index, id := range q.ids {
		if wanted[id] {
			q.ids[index] = ordered[next]
			next++
		}
	}
}

func (q *taskQueue) notify() {
	select {
	case q.wake <- struct{}{}:
	default:
	}
}
