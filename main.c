#include <sys/time.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <omp.h>

#define swap(d,a,b) {uint32_t dt = d[b]; d[b] = d[a]; d[a] = dt;}
#ifndef THRESHOLD
#define THRESHOLD 1000
#endif

static uint32_t partition(uint32_t *a, uint32_t len)
{
    uint32_t mid = len / 2;
    swap(a, 0, mid);
    uint32_t pivot = a[0];
    uint32_t p = 0;
    uint32_t q = len - 1;

    while (p < q)
    {
        while (p < q && a[q] > pivot)
            q--;
        while (p < q && a[p] <= pivot)
            p++;
        if (p < q)
            swap(a, p, q);
    }
    swap(a, 0, q);
    return q;
}

static void QSortSeq(uint32_t *data, uint32_t start, uint32_t end)
{
    if (start + 1 >= end)
        return;

    if (start + 2 == end)
    {
        if (data[start] > data[start + 1])
            swap(data, start, start + 1);
        return;
    }

    uint32_t size = end - start;
    uint32_t store = start + partition(data + start, size);
    QSortSeq(data, start, store);
    QSortSeq(data, store + 1, end);
}

void QSortPar(uint32_t *data, uint32_t start, uint32_t end)
{
    uint32_t size = end - start;
    if (size <= THRESHOLD)
    {
        QSortSeq(data, start, end);
        return;
    }

    if (start + 1 >= end)
        return;

    uint32_t store = start + partition(data + start, size);

    #pragma omp task shared(data) firstprivate(start, store) if (size > THRESHOLD)
    QSortPar(data, start, store);

    #pragma omp task shared(data) firstprivate(store, end) if (size > THRESHOLD)
    QSortPar(data, store + 1, end);

    #pragma omp taskwait
}

void quicksort(uint32_t *data, uint32_t size)
{
    #pragma omp parallel
    {
        #pragma omp single nowait
        {
            QSortPar(data, 0, size);
        }
    }
}


double wtime()
{
    struct timeval t;
    gettimeofday(&t, NULL);
    return (double)t.tv_sec + (double)t.tv_usec * 1E-6;
}

int getrand(int min, int max)
{
    return (double)rand() / (RAND_MAX + 1.0) * (max - min) + min;
}

int main(int argc, char **argv)
{
    uint32_t LEN, i, HASH = 0;
    int Gen = 0;

    if (argc != 3)
    {
        printf(":(\n");
        return 1;
    }

    LEN = atol(argv[1]);
    Gen = atoi(argv[2]);

    if (Gen < 0 || Gen > 4 || LEN < 2)
    {
        printf("\n\tСломано!\n");
        return 1;
    }

    uint32_t *Mas = malloc(LEN * sizeof(uint32_t));
    if (Mas == NULL)
        return 2;

    double t;

    if (Gen == 1)
    {
        for (i = 0; i < LEN; i++)
        {
            Mas[i] = getrand(1, 10000) * getrand(1, 10000);
            HASH += Mas[i];
        }
        printf("\tСоздан случайный массив из %u элементов\n", LEN);
    }
    else if (Gen == 2)
    {
        for (i = 0; i < LEN; i++)
        {
            Mas[i] = LEN - i;
            HASH += Mas[i];
        }
        printf("\tСоздан массив отсортированный по убыванию из %u элементов\n", LEN);
    }
    else if (Gen == 3)
    {
        for (i = 0; i < LEN; i++)
        {
            Mas[i] = i;
            HASH += Mas[i];
        }
        printf("\tСоздан массив отсортированный по возрастанию из %u элементов\n", LEN);
    }
    else
    {
        for (i = 0; i < LEN; i++)
        {
            Mas[i] = i;
            HASH += Mas[i];
        }
        printf("\tСоздан массив почти отсортированный по возрастанию из %u элементов\n", LEN);
    }

    t = wtime();
    quicksort(Mas, LEN);
    t = wtime() - t;

    printf("\tВремя выполнения: %.6f секунд\n", t);

    for (i = 0; i + 1 < LEN; i++)
    {
        HASH -= Mas[i];
        if (Mas[i] > Mas[i + 1])
        {
            printf("\tМассив НЕ отсортирован по неубыванию!\n");
            free(Mas);
            return 3;
        }
    }
    printf("\tМассив отсортирован по неубыванию\n");
    HASH -= Mas[LEN - 1];
    if (HASH == 0)
        printf("\tМассив не искажен\n");
    else
        printf("\tМассив ИСКАЖЕН!\n");

    free(Mas);
    return 0;
}
