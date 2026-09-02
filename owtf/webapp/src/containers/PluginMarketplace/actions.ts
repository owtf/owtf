import {
  LOAD_COMMUNITY_PLUGINS,
  LOAD_COMMUNITY_PLUGINS_SUCCESS,
  LOAD_COMMUNITY_PLUGINS_ERROR,
  LOAD_COMMUNITY_PLUGIN_DETAIL,
  LOAD_COMMUNITY_PLUGIN_DETAIL_SUCCESS,
  LOAD_COMMUNITY_PLUGIN_DETAIL_ERROR,
  UPLOAD_COMMUNITY_PLUGIN,
  UPLOAD_COMMUNITY_PLUGIN_SUCCESS,
  UPLOAD_COMMUNITY_PLUGIN_ERROR,
  CLEAR_UPLOAD_STATE,
  SET_FILTER
} from "./constants";
import { PluginListParams } from "./api";

export const loadCommunityPlugins = (params: PluginListParams = {}) => ({
  type: LOAD_COMMUNITY_PLUGINS,
  params
});

export const loadCommunityPluginsSuccess = (data: any) => ({
  type: LOAD_COMMUNITY_PLUGINS_SUCCESS,
  data
});

export const loadCommunityPluginsError = (error: string) => ({
  type: LOAD_COMMUNITY_PLUGINS_ERROR,
  error
});

export const loadCommunityPluginDetail = (id: number) => ({
  type: LOAD_COMMUNITY_PLUGIN_DETAIL,
  id
});

export const loadCommunityPluginDetailSuccess = (plugin: any) => ({
  type: LOAD_COMMUNITY_PLUGIN_DETAIL_SUCCESS,
  plugin
});

export const loadCommunityPluginDetailError = (error: string) => ({
  type: LOAD_COMMUNITY_PLUGIN_DETAIL_ERROR,
  error
});

export const uploadCommunityPlugin = (formData: FormData) => ({
  type: UPLOAD_COMMUNITY_PLUGIN,
  formData
});

export const uploadCommunityPluginSuccess = (plugin: any) => ({
  type: UPLOAD_COMMUNITY_PLUGIN_SUCCESS,
  plugin
});

export const uploadCommunityPluginError = (error: any) => ({
  type: UPLOAD_COMMUNITY_PLUGIN_ERROR,
  error
});

export const clearUploadState = () => ({ type: CLEAR_UPLOAD_STATE });

export const setFilter = (filter: Partial<PluginListParams>) => ({
  type: SET_FILTER,
  filter
});
