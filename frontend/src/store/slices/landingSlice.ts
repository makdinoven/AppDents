import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface StateProps {
  newPrice: number;
  oldPrice: number;
  lessonsCount: string;
  isModalOpen: boolean;
}

const initialState: StateProps = {
  newPrice: 0,
  oldPrice: 0,
  lessonsCount: "",
  isModalOpen: false,
};

const landingSlice = createSlice({
  name: "landing",
  initialState,
  reducers: {
    setPrices(
      state,
      action: PayloadAction<{ newPrice: number; oldPrice: number }>,
    ) {
      state.newPrice = action.payload.newPrice;
      state.oldPrice = action.payload.oldPrice;
    },
    setLessonsCount(state, action: PayloadAction<{ lessonsCount: string }>) {
      state.lessonsCount = action.payload.lessonsCount;
    },
    openModal(state) {
      state.isModalOpen = true;
    },
    closeModal(state) {
      state.isModalOpen = false;
    },
  },
});

export const { setPrices, openModal, closeModal, setLessonsCount } =
  landingSlice.actions;
export const landingReducer = landingSlice.reducer;
