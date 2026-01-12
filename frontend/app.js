/**
 * 뉴스 트렌드 대시보드 - 프론트엔드 JavaScript
 */

const API_BASE = '';

// 차트 인스턴스
let categoryChart = null;
let sourceChart = null;

// 현재 선택된 카테고리
let currentCategory = 'all';

/**
 * 초기화
 */
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadTrends();
    loadNews();
});

/**
 * 카테고리 목록 로드
 */
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/api/categories`);
        const result = await response.json();

        if (result.success) {
            renderCategoryButtons(result.data);
        }
    } catch (error) {
        console.error('카테고리 로드 실패:', error);
    }
}

/**
 * 카테고리 버튼 렌더링
 */
function renderCategoryButtons(categories) {
    const container = document.getElementById('categoryButtons');
    container.innerHTML = '<button class="category-btn active" data-category="all" onclick="filterByCategory(\'all\')">전체</button>';

    categories.forEach(category => {
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.dataset.category = category;
        btn.textContent = category;
        btn.onclick = () => filterByCategory(category);
        container.appendChild(btn);
    });
}

/**
 * 트렌드 데이터 로드
 */
async function loadTrends() {
    try {
        const response = await fetch(`${API_BASE}/api/trends`);
        const result = await response.json();

        if (result.success) {
            renderStats(result.data);
            renderCategoryChart(result.data.categories);
            renderSourceChart(result.data.sources);
            renderKeywords(result.data.keywords);
        }
    } catch (error) {
        console.error('트렌드 로드 실패:', error);
    }
}

/**
 * 통계 렌더링
 */
function renderStats(data) {
    // 총 뉴스 수 계산
    const totalNews = data.categories.reduce((sum, item) => sum + item.count, 0);
    document.getElementById('totalNews').textContent = totalNews;

    // 카테고리 수
    document.getElementById('totalCategories').textContent = data.categories.length;

    // 인기 키워드
    if (data.keywords.length > 0) {
        document.getElementById('topKeyword').textContent = data.keywords[0].keyword;
    }
}

/**
 * 카테고리 차트 렌더링
 */
function renderCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart').getContext('2d');

    if (categoryChart) {
        categoryChart.destroy();
    }

    const colors = [
        '#ee9ca7', '#ffdde1', '#fcb69f', '#ffecd2',
        '#f8b4b4', '#e8848f', '#ffb6c1'
    ];

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                data: categories.map(c => c.count),
                backgroundColor: colors.slice(0, categories.length),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#fff',
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

/**
 * 출처 차트 렌더링
 */
function renderSourceChart(sources) {
    const ctx = document.getElementById('sourceChart').getContext('2d');

    if (sourceChart) {
        sourceChart.destroy();
    }

    sourceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sources.map(s => s.source),
            datasets: [{
                label: '뉴스 수',
                data: sources.map(s => s.count),
                backgroundColor: 'rgba(238, 156, 167, 0.7)',
                borderColor: '#ee9ca7',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    ticks: { color: '#a0a0a0' },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                },
                y: {
                    ticks: { color: '#a0a0a0' },
                    grid: { color: 'rgba(255,255,255,0.1)' }
                }
            }
        }
    });
}

/**
 * 키워드 렌더링
 */
function renderKeywords(keywords) {
    const container = document.getElementById('keywordsContainer');
    container.innerHTML = '';

    keywords.forEach(item => {
        const tag = document.createElement('span');
        tag.className = 'keyword-tag';
        tag.innerHTML = `${item.keyword}<span class="count">${item.total_count}</span>`;
        container.appendChild(tag);
    });
}

/**
 * 뉴스 로드
 */
async function loadNews(category = null) {
    const container = document.getElementById('newsList');
    container.innerHTML = '<div class="loading">로딩 중...</div>';

    try {
        let url = `${API_BASE}/api/news`;
        if (category && category !== 'all') {
            url += `?category=${encodeURIComponent(category)}`;
        }

        const response = await fetch(url);
        const result = await response.json();

        if (result.success) {
            renderNews(result.data);
        }
    } catch (error) {
        console.error('뉴스 로드 실패:', error);
        container.innerHTML = '<div class="loading">뉴스를 불러올 수 없습니다.</div>';
    }
}

/**
 * 뉴스 목록 렌더링
 */
function renderNews(newsList) {
    const container = document.getElementById('newsList');

    if (newsList.length === 0) {
        container.innerHTML = '<div class="loading">뉴스가 없습니다.</div>';
        return;
    }

    container.innerHTML = newsList.map(news => `
        <div class="news-item">
            <h4>${escapeHtml(news.title)}</h4>
            <p>${escapeHtml(news.description || '')}</p>
            <div class="news-meta">
                <span class="news-source">${escapeHtml(news.source)}</span>
                <span class="news-category">${escapeHtml(news.category)}</span>
                <span class="news-date">${formatDate(news.published_at)}</span>
            </div>
        </div>
    `).join('');
}

/**
 * 카테고리 필터
 */
function filterByCategory(category) {
    currentCategory = category;

    // 버튼 활성화 상태 업데이트
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.category === category);
    });

    // 뉴스 다시 로드
    loadNews(category);
}

/**
 * 데이터 새로고침
 */
async function refreshData() {
    const btn = document.querySelector('.refresh-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="icon" style="animation: spin 1s linear infinite;">&#8635;</span> 수집 중...';

    try {
        const response = await fetch(`${API_BASE}/api/refresh`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            // 모든 데이터 다시 로드
            await loadTrends();
            await loadNews(currentCategory);
            alert(result.message);
        } else {
            alert('새로고침 실패: ' + result.error);
        }
    } catch (error) {
        console.error('새로고침 실패:', error);
        alert('서버에 연결할 수 없습니다.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="icon">&#8635;</span> 새로고침';
    }
}

/**
 * HTML 이스케이프
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * 날짜 포맷
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 스핀 애니메이션 추가
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
