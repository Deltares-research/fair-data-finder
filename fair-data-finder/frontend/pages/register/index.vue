<template>
  <v-sheet class="d-flex flex-column">
    <!-- Header Section -->
    <div class="pa-4">
      <v-row class="mb-4">
        <v-col cols="12" class="d-flex justify-space-between align-end">
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">
              Registered data
            </h1>
            <p class="text-body-2 text-grey-darken-1">
              List of datasets registrations, which you are allowed to edit.
            </p>
          </div>
          <v-btn
            color="grey-darken-1"
            variant="flat"
            prepend-icon="mdi-plus"
            class="text-white"
            to="/register/create"
          >
            Register new dataset
          </v-btn>
        </v-col>
      </v-row>
    </div>

    <div class="flex-grow-1 d-flex flex-column py-4 px-6" style="min-height: 0;">
      <!-- Loading state -->
      <div
        v-if="store.isLoading"
        class="d-flex justify-center align-center"
        style="min-height: 200px;"
      >
        <v-progress-circular
          indeterminate
          color="primary"
        />
      </div>

      <!-- Error state -->
      <div v-else-if="store.error" class="d-flex justify-center align-center pa-4">
        <v-alert type="error" variant="tonal">
          {{ store.error }}
        </v-alert>
      </div>

      <!-- Data table -->
      <v-data-table
        v-else
        :headers="headers"
        :items="paginatedDatasets"
        :items-per-page="itemsPerPage"
        :page="1"
        class="elevation-0 flex-grow-1"
        hide-default-footer
        :sort-by="sortByOptions"
        @update:sort-by="handleSortUpdate"
      >
        <!-- Description column with truncation -->
        <!-- eslint-disable-next-line vue/valid-v-slot -->
        <template #[`item.description`]="{ item }">
          <span
            class="text-truncate"
            style="max-width: 300px; display: inline-block;"
            :title="item.description"
          >
            {{ item.description }}
          </span>
        </template>

        <!-- Storage location column -->
        <!-- eslint-disable-next-line vue/valid-v-slot -->
        <template #[`item.storageLocation`]="{ item }">
          <span>{{ item.storageLocation || '—' }}</span>
        </template>

        <!-- Date column -->
        <!-- eslint-disable-next-line vue/valid-v-slot -->
        <template #[`item.date`]="{ item }">
          <span>{{ formatDate(item.date) }}</span>
        </template>

        <!-- Edit column -->
        <!-- eslint-disable-next-line vue/valid-v-slot -->
        <template #[`item.edit`]="{ item }">
          <v-btn
            variant="text"
            size="small"
            prepend-icon="mdi-pencil"
            class="text-capitalize"
            @click.stop="handleEdit(item)"
          >
            Edit
          </v-btn>
        </template>

        <!-- Delete column -->
        <!-- eslint-disable-next-line vue/valid-v-slot -->
        <template #[`item.delete`]="{ item }">
          <v-btn
            variant="text"
            size="small"
            prepend-icon="mdi-delete"
            class="text-capitalize"
            @click.stop="handleDelete(item)"
          >
            Delete
          </v-btn>
        </template>
      </v-data-table>

      <!-- Pagination -->
      <div v-if="!store.isLoading && !store.error" class="d-flex justify-end align-center mt-4">
        <v-btn
          :disabled="!store.hasPreviousPage"
          variant="outlined"
          class="mr-2"
          @click="previousPage"
        >
          Previous
        </v-btn>
        <span class="text-body-2 mx-2">Page {{ store.currentPage }}</span>
        <v-btn
          :disabled="!store.hasNextPage"
          variant="outlined"
          @click="nextPage"
        >
          Next
        </v-btn>
      </div>
    </div>
  </v-sheet>
</template>

<script setup>
  import { ref, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import dateFormat from 'dateformat'
  import { useRegisterStore } from '~/stores/register'

  // Component name for Vue linting
  defineOptions({
    name: 'RegisterIndexPage'
  })

  // Router
  const router = useRouter()

  // Store
  const store = useRegisterStore()

  // Table configuration
  const headers = [
    { title: 'Title', key: 'title', sortable: true },
    { title: 'Description', key: 'description', sortable: true },
    { title: 'Domain', key: 'domain', sortable: true },
    { title: 'Storage location', key: 'storageLocation', sortable: true },
    { title: 'Date', key: 'date', sortable: true },
    { title: '', key: 'edit', sortable: false },
    { title: '', key: 'delete', sortable: false }
  ]

  const sortByOptions = ref([{ key: 'date', order: 'desc' }])

  // Maps Vuetify data-table column keys to the STAC field paths accepted by
  // the Sort extension, so the header keys stay decoupled from STAC paths.
  const SORT_FIELD_BY_COLUMN = {
    title: 'properties.title',
    description: 'properties.description',
    domain: 'collection',
    storageLocation: 'properties.storagelocation',
    date: 'properties.datetime',
  }

  // Handle sort updates from Vuetify data table. Sorting is delegated to the
  // API (STAC sortby), so this pushes the new sort to the store instead of
  // reordering the currently loaded page in-memory.
  function handleSortUpdate(value) {
    if (value && value.length > 0) {
      const firstSort = value[0]
      const order = firstSort.order || 'asc'
      sortByOptions.value = [{ key: firstSort.key, order }]

      const field = SORT_FIELD_BY_COLUMN[firstSort.key]
      if (field) {
        store.setSortBy([{ field, direction: order }])
      }
    } else {
      sortByOptions.value = []
    }
  }

  // Map STAC items to table format
  const mappedDatasets = computed(() => {
    return store.items.map(item => ({
      id: item.id,
      title: item.properties?.title || '—',
      description: item.properties?.description || '—',
      domain: item.collection || '—',
      storageLocation: item.properties?.storagelocation || '—',
      date: item.properties?.datetime ? new Date(item.properties.datetime) : null,
      // Keep original item for edit/delete operations
      _original: item
    }))
  })

  const itemsPerPage = computed(() => store.itemsPerPage)

  const paginatedDatasets = computed(() => {
    // The API returns items already paginated and sorted (STAC sortby), so
    // no further client-side pagination or sorting is needed here.
    return mappedDatasets.value
  })

  // Methods
  function formatDate(date) {
    if (!date) return '—'
    return dateFormat(date, 'dd-mm-yyyy HH:MM:ss')
  }

  async function previousPage() {
    await store.previousPage()
  }

  async function nextPage() {
    await store.nextPage()
  }

  function handleEdit(item) {
    // Navigate to edit page using item.id
    router.push(`/register/${item.id}/edit`)
  }

  function handleDelete(item) {
    // Navigate to delete confirmation page
    router.push(`/register/${item.id}/delete`)
  }

  // Fetch items on mount. If the list was already loaded on a previous visit
  // (the Pinia store persists across navigation), show the cached data
  // immediately and refresh it silently in the background instead of
  // blanking the table behind a spinner every time this tab is revisited.
  store.fetchItems(null, { silent: store.hasLoaded })
</script>

<style scoped>

  .text-truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :deep(.v-data-table) {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    border: 1px solid rgba(0, 0, 0, 0.12);
  }

</style>
